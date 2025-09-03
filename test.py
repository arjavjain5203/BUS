import os
import mysql.connector
from dotenv import load_dotenv

# --------------------------
# 1. Load environment vars
# --------------------------
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# --------------------------
# 2. Connect to MySQL
# --------------------------
conn = mysql.connector.connect(
    host=DB_HOST,
    port=DB_PORT,
    user=DB_USER,
    password=DB_PASSWORD
)
cursor = conn.cursor()

# --------------------------
# 3. Drop + Create Database
# --------------------------
cursor.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
cursor.execute(f"CREATE DATABASE {DB_NAME}")
cursor.execute(f"USE {DB_NAME}")

print(f"✅ Database {DB_NAME} recreated successfully!")

# --------------------------
# 4. Create Tables
# --------------------------
schema_queries = [
    """
    CREATE TABLE users (
        user_id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        age INT,
        mobile_no VARCHAR(15) UNIQUE,
        email VARCHAR(100) UNIQUE,
        region_of_commute VARCHAR(100),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE busstops (
        stop_id INT AUTO_INCREMENT PRIMARY KEY,
        stop_name VARCHAR(100) NOT NULL,
        location VARCHAR(255),
        region VARCHAR(100)
    )
    """,
    """
    CREATE TABLE routes (
        route_id INT AUTO_INCREMENT PRIMARY KEY,
        route_name VARCHAR(100) NOT NULL,
        start_stop_id INT,
        end_stop_id INT,
        distance_km FLOAT,
        FOREIGN KEY (start_stop_id) REFERENCES busstops(stop_id),
        FOREIGN KEY (end_stop_id) REFERENCES busstops(stop_id)
    )
    """,
    """
    CREATE TABLE buses (
        bus_id INT AUTO_INCREMENT PRIMARY KEY,
        bus_number VARCHAR(50) NOT NULL,
        capacity INT,
        current_location VARCHAR(255),
        route_id INT,
        status VARCHAR(50),
        FOREIGN KEY (route_id) REFERENCES routes(route_id)
    )
    """,
    """
    CREATE TABLE drivers (
        driver_id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        mobile_no VARCHAR(15) UNIQUE,
        bus_id INT,
        location VARCHAR(255),
        shift_start TIME,
        shift_end TIME,
        FOREIGN KEY (bus_id) REFERENCES buses(bus_id)
    )
    """,
    """
    CREATE TABLE tickets (
        ticket_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        bus_id INT,
        route_id INT,
        source_stop_id INT,
        destination_stop_id INT,
        fare FLOAT,
        purchase_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id),
        FOREIGN KEY (bus_id) REFERENCES buses(bus_id),
        FOREIGN KEY (route_id) REFERENCES routes(route_id),
        FOREIGN KEY (source_stop_id) REFERENCES busstops(stop_id),
        FOREIGN KEY (destination_stop_id) REFERENCES busstops(stop_id)
    )
    """,
    """
    CREATE TABLE notifications (
        notification_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        type VARCHAR(50),
        message TEXT,
        sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    """,
    """
    CREATE TABLE chatlogs (
        chat_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        message_text TEXT,
        response_text TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    """,
    """
    CREATE TABLE routestops (
        id INT AUTO_INCREMENT PRIMARY KEY,
        route_id INT,
        stop_id INT,
        stop_order INT,
        FOREIGN KEY (route_id) REFERENCES routes(route_id),
        FOREIGN KEY (stop_id) REFERENCES busstops(stop_id)
    )
    """
]

for query in schema_queries:
    cursor.execute(query)

print("✅ Tables created successfully!")

# --------------------------
# 5. Seed Sample Data
# --------------------------
seed_queries = [
    # Users
    """
    INSERT INTO users (name, age, mobile_no, email, region_of_commute)
    VALUES 
    ('Arjun Singh', 24, '9876543210', 'arjun@example.com', 'Chandigarh'),
    ('Simran Kaur', 29, '9876501234', 'simran@example.com', 'Ludhiana'),
    ('Harpreet Gill', 35, '9812345678', 'harpreet@example.com', 'Amritsar')
    """,
    # Bus Stops
    """
    INSERT INTO busstops (stop_name, location, region)
    VALUES 
    ('ISBT Chandigarh', 'Sector 43, Chandigarh', 'Chandigarh'),
    ('Sector 17 Bus Stand', 'Sector 17, Chandigarh', 'Chandigarh'),
    ('Ludhiana Bus Stand', 'Gill Road, Ludhiana', 'Ludhiana'),
    ('Jalandhar Bus Stand', 'Nakodar Road, Jalandhar', 'Jalandhar'),
    ('Amritsar Bus Stand', 'Grand Trunk Road, Amritsar', 'Amritsar'),
    ('Patiala Bus Stand', 'Bhupindra Road, Patiala', 'Patiala')
    """,
    # Routes
    """
    INSERT INTO routes (route_name, start_stop_id, end_stop_id, distance_km)
    VALUES
    ('Chandigarh to Ludhiana', 1, 3, 100.5),
    ('Chandigarh to Jalandhar', 1, 4, 150.0),
    ('Ludhiana to Amritsar', 3, 5, 135.0),
    ('Patiala to Chandigarh', 6, 1, 75.0)
    """,
    # Buses
    """
    INSERT INTO buses (bus_number, capacity, current_location, route_id, status)
    VALUES
    ('PB10AB1234', 50, 'On route near Kharar', 1, 'Running'),
    ('PB11XY5678', 45, 'Ludhiana Bus Stand', 3, 'Idle'),
    ('PB09CD4321', 52, 'On route near Phagwara', 2, 'Running'),
    ('PB39EF9876', 40, 'Patiala Bus Stand', 4, 'Idle')
    """,
    # Drivers
    """
    INSERT INTO drivers (name, mobile_no, bus_id, location, shift_start, shift_end)
    VALUES
    ('Rajesh Kumar', '9876123456', 1, 'On route', '06:00:00', '14:00:00'),
    ('Baljit Singh', '9876234567', 2, 'Ludhiana Bus Stand', '08:00:00', '16:00:00'),
    ('Sukhdeep Kaur', '9876345678', 3, 'On route', '14:00:00', '22:00:00'),
    ('Gurpreet Singh', '9876456789', 4, 'Patiala Bus Stand', '07:00:00', '15:00:00')
    """,
    # RouteStops
    """
    INSERT INTO routestops (route_id, stop_id, stop_order)
    VALUES
    (1, 1, 1), (1, 2, 2), (1, 3, 3),
    (2, 1, 1), (2, 2, 2), (2, 4, 3),
    (3, 3, 1), (3, 4, 2), (3, 5, 3),
    (4, 6, 1), (4, 2, 2), (4, 1, 3)
    """,
    # Tickets
    """
    INSERT INTO tickets (user_id, bus_id, route_id, source_stop_id, destination_stop_id, fare)
    VALUES
    (1, 1, 1, 1, 3, 150.0),
    (2, 3, 2, 1, 4, 220.0),
    (3, 2, 3, 3, 5, 180.0)
    """,
    # Notifications
    """
    INSERT INTO notifications (user_id, type, message)
    VALUES
    (1, 'ETA Alert', 'Your bus PB10AB1234 will arrive at Sector 17 in 5 mins'),
    (2, 'Booking Confirmed', 'Your ticket Chandigarh → Jalandhar has been confirmed'),
    (3, 'Delay Alert', 'Bus PB11XY5678 is running 15 mins late from Ludhiana')
    """,
    # Chatlogs
    """
    INSERT INTO chatlogs (user_id, message_text, response_text)
    VALUES
    (1, 'Next bus from ISBT Chandigarh to Ludhiana?', 'Bus PB10AB1234 → ETA 10 min, occupancy 60%'),
    (2, 'When is the first bus to Jalandhar tomorrow?', 'First bus leaves ISBT Chandigarh at 06:00 AM'),
    (3, 'How crowded is the Ludhiana bus?', 'Bus PB11XY5678 occupancy is medium')
    """
]

for query in seed_queries:
    cursor.execute(query)

conn.commit()
print("✅ Sample data inserted successfully!")

# Close connection
cursor.close()
conn.close()
