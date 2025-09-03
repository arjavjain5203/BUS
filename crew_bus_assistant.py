# import os
# import datetime
# import mysql.connector
# from dotenv import load_dotenv
# from crewai import Agent, Task, Crew, Process
# from google.generativeai import configure, GenerativeModel

# # -------------------------
# # 1. Load .env config
# # -------------------------
# load_dotenv()

# API_KEY = os.getenv("GEMINI_API_KEY")
# DB_HOST = os.getenv("DB_HOST")
# DB_PORT = int(os.getenv("DB_PORT", "3306"))
# DB_USER = os.getenv("DB_USER")
# DB_PASSWORD = os.getenv("DB_PASSWORD")
# DB_NAME = os.getenv("DB_NAME")

# # -------------------------
# # 2. Configure Gemini
# # -------------------------
# configure(api_key=API_KEY)
# gemini_model = GenerativeModel("gemini-1.5-flash")

# # -------------------------
# # 3. Configure MySQL
# # -------------------------
# db = mysql.connector.connect(
#     host=DB_HOST,
#     port=DB_PORT,
#     user=DB_USER,
#     password=DB_PASSWORD,
#     database=DB_NAME
# )
# cursor = db.cursor(dictionary=True)

# # -------------------------
# # 4. Define Schema Prompt
# # -------------------------
# SCHEMA_PROMPT = """
# You are a SQL assistant for a Punjab transport database.
# Rules:
# - Only use these tables and columns:
#   users(user_id, name, age, mobile_no, email, region_of_commute, created_at)
#   busstops(stop_id, stop_name, location, region)
#   routes(route_id, route_name, start_stop_id, end_stop_id, distance_km)
#   buses(bus_id, bus_number, capacity, current_location, route_id, status)
#   drivers(driver_id, name, mobile_no, bus_id, location, shift_start, shift_end)
#   tickets(ticket_id, user_id, bus_id, route_id, source_stop_id, destination_stop_id, fare, purchase_time)
#   notifications(notification_id, user_id, type, message, sent_at)
#   chatlogs(chat_id, user_id, message_text, response_text, created_at)
#   routestops(id, route_id, stop_id, stop_order)

# - Do NOT use columns that don’t exist.
# - Always use LIKE instead of = when filtering stop_name or location.
# - For bus availability queries, return bus_number, route_name, current_location, and status.
# - If data is not found, return an empty result (do not invent).
# - Always include LIMIT 3 to avoid large results.

# Examples:

# User: Next bus from ISBT Chandigarh to Ludhiana?
# SQL:
# SELECT b.bus_number, r.route_name, b.current_location, b.status
# FROM routes r
# JOIN buses b ON r.route_id = b.route_id
# JOIN routestops rs1 ON r.route_id = rs1.route_id
# JOIN busstops bs1 ON rs1.stop_id = bs1.stop_id
# JOIN routestops rs2 ON r.route_id = rs2.route_id
# JOIN busstops bs2 ON rs2.stop_id = bs2.stop_id
# WHERE bs1.stop_name LIKE '%Chandigarh%'
#   AND bs2.stop_name LIKE '%Ludhiana%'
#   AND b.status = 'Running'
# LIMIT 3;
# """

# # -------------------------
# # 5. Define Agents
# # -------------------------

# # SQL Generator Agent
# sql_agent = Agent(
#     role="SQL Query Generator",
#     goal="Generate safe SQL queries for transport database queries",
#     backstory="Expert in translating natural language commute queries into MySQL queries using the Punjab schema.",
#     llm=gemini_model,
#     verbose=True
# )

# # DB Executor Agent
# def run_query(task_input):
#     sql = task_input["sql"]
#     try:
#         cursor.execute(sql)
#         return cursor.fetchall()
#     except Exception as e:
#         return {"error": str(e)}

# db_agent = Agent(
#     role="Database Executor",
#     goal="Execute SQL queries safely against MySQL",
#     backstory="Executes SQL queries and retrieves results.",
#     tools=[run_query],
#     verbose=True
# )

# # Response Formatter Agent
# formatter_agent = Agent(
#     role="Response Formatter",
#     goal="Format database results into a user-friendly reply for SMS/WhatsApp.",
#     backstory="Takes structured SQL results and converts them into natural responses.",
#     llm=gemini_model,
#     verbose=True
# )

# # -------------------------
# # 6. Define Tasks
# # -------------------------
# generate_sql_task = Task(
#     description="Generate SQL for user query: {user_input}\nUse the schema and examples.\nReturn only SQL.",
#     agent=sql_agent,
#     expected_output="A valid SQL query string."
# )

# execute_sql_task = Task(
#     description="Run the SQL query and return the raw results.",
#     agent=db_agent,
#     expected_output="List of rows from MySQL database."
# )

# format_response_task = Task(
#     description="Format the SQL results for user: {user_input}\nResults: {sql_results}",
#     agent=formatter_agent,
#     expected_output="A clear SMS/WhatsApp friendly response."
# )

# # -------------------------
# # 7. Build Crew Pipeline
# # -------------------------
# crew = Crew(
#     agents=[sql_agent, db_agent, formatter_agent],
#     tasks=[generate_sql_task, execute_sql_task, format_response_task],
#     process=Process.sequential
# )

# # -------------------------
# # 8. Chat Loop
# # -------------------------
# def chat_loop(user_id=1):
#     print("🤖 CrewAI Punjab Bus Assistant (type 'exit' to quit)\n")
#     while True:
#         user_input = input("You: ")
#         if user_input.lower() in ["exit", "quit"]:
#             break

#         result = crew.kickoff(inputs={"user_input": user_input})
#         response_text = str(result)

#         # Print response
#         print("Bot:", response_text)

#         # Save chat in DB
#         insert_chat = """
#             INSERT INTO chatlogs (user_id, message_text, response_text, created_at)
#             VALUES (%s, %s, %s, %s)
#         """
#         cursor.execute(insert_chat, (user_id, user_input, response_text, datetime.datetime.now()))
#         db.commit()

# if __name__ == "__main__":
#     chat_loop()







import os
import datetime
import mysql.connector
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from google.generativeai import configure, GenerativeModel
from collections import deque
from crewai_tools import tool


# -------------------------
# 1. Load .env config
# -------------------------
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# -------------------------
# 2. Configure Gemini
# -------------------------
configure(api_key=API_KEY)
gemini_model = GenerativeModel("gemini-1.5-flash")

# -------------------------
# 3. Configure MySQL
# -------------------------
db = mysql.connector.connect(
    host=DB_HOST,
    port=DB_PORT,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME
)
cursor = db.cursor(dictionary=True)

# -------------------------
# 4. Chat Memory
# -------------------------
chat_history = deque(maxlen=5)  # keep last 5 interactions

def get_chat_context():
    """Format last few turns into a context string."""
    return "\n".join([f"User: {u}\nBot: {b}" for u, b in chat_history])

# -------------------------
# 5. Define Schema Prompt
# -------------------------
SCHEMA_PROMPT = """
You are a SQL assistant for a Punjab transport database.
Rules:
- Only use these tables and columns:
  users(user_id, name, age, mobile_no, email, region_of_commute, created_at)
  busstops(stop_id, stop_name, location, region)
  routes(route_id, route_name, start_stop_id, end_stop_id, distance_km)
  buses(bus_id, bus_number, capacity, current_location, route_id, status)
  drivers(driver_id, name, mobile_no, bus_id, location, shift_start, shift_end)
  tickets(ticket_id, user_id, bus_id, route_id, source_stop_id, destination_stop_id, fare, purchase_time)
  notifications(notification_id, user_id, type, message, sent_at)
  chatlogs(chat_id, user_id, message_text, response_text, created_at)
  routestops(id, route_id, stop_id, stop_order)

- Do NOT use columns that don’t exist.
- Always use LIKE instead of = when filtering stop_name or location.
- For bus availability queries, return bus_number, route_name, current_location, and status.
- If data is not found, return an empty result (do not invent).
- Always include LIMIT 3 to avoid large results.

Examples:

User: Next bus from ISBT Chandigarh to Ludhiana?
SQL:
SELECT b.bus_number, r.route_name, b.current_location, b.status
FROM routes r
JOIN buses b ON r.route_id = b.route_id
JOIN routestops rs1 ON r.route_id = rs1.route_id
JOIN busstops bs1 ON rs1.stop_id = bs1.stop_id
JOIN routestops rs2 ON r.route_id = rs2.route_id
JOIN busstops bs2 ON rs2.stop_id = bs2.stop_id
WHERE bs1.stop_name LIKE '%Chandigarh%'
  AND bs2.stop_name LIKE '%Ludhiana%'
  AND b.status = 'Running'
LIMIT 3;
"""

# -------------------------
# 6. Define Agents
# -------------------------

# SQL Generator Agent
sql_agent = Agent(
    role="SQL Query Generator",
    goal="Generate safe SQL queries for transport database queries",
    backstory="Expert in translating natural language commute queries into MySQL queries using the Punjab schema.",
    llm=gemini_model,
    verbose=True
)

# DB Executor Agent
@tool("run_query")
def run_query(sql: str) -> str:
    """
    Executes a SQL query on the Punjab transport database and returns results as text.
    """
    try:
        cursor.execute(sql)
        results = cursor.fetchall()
        return str(results)
    except Exception as e:
        return f"Error: {str(e)}"


db_agent = Agent(
    role="Database Executor",
    goal="Execute SQL queries safely against MySQL",
    backstory="Executes SQL queries and retrieves results.",
    tools=[run_query],
    verbose=True
)

# Response Formatter Agent
formatter_agent = Agent(
    role="Response Formatter",
    goal="Format database results into a user-friendly reply for SMS/WhatsApp.",
    backstory="Takes structured SQL results and converts them into natural responses.",
    llm=gemini_model,
    verbose=True
)

# -------------------------
# 7. Define Tasks
# -------------------------
generate_sql_task = Task(
    description=(
        f"{SCHEMA_PROMPT}\n"
        "Conversation so far:\n{{chat_context}}\n\n"
        "New user query: {{user_input}}\n"
        "Write only the SQL query."
    ),
    agent=sql_agent,
    expected_output="A valid SQL query string."
)

execute_sql_task = Task(
    description="Run the SQL query and return the raw results.",
    agent=db_agent,
    expected_output="List of rows from MySQL database."
)

format_response_task = Task(
    description="Format the SQL results for user: {user_input}\nResults: {sql_results}",
    agent=formatter_agent,
    expected_output="A clear SMS/WhatsApp friendly response."
)

# -------------------------
# 8. Build Crew Pipeline
# -------------------------
crew = Crew(
    agents=[sql_agent, db_agent, formatter_agent],
    tasks=[generate_sql_task, execute_sql_task, format_response_task],
    process=Process.sequential
)

# -------------------------
# 9. Chat Loop
# -------------------------
def chat_loop(user_id=1):
    print("🤖 CrewAI Punjab Bus Assistant (with memory) (type 'exit' to quit)\n")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        result = crew.kickoff(inputs={
            "user_input": user_input,
            "chat_context": get_chat_context()
        })
        response_text = str(result)

        # Print response
        print("Bot:", response_text)

        # Save in history (for memory)
        chat_history.append((user_input, response_text))

        # Save in DB
        insert_chat = """
            INSERT INTO chatlogs (user_id, message_text, response_text, created_at)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(insert_chat, (user_id, user_input, response_text, datetime.datetime.now()))
        db.commit()

if __name__ == "__main__":
    chat_loop()
