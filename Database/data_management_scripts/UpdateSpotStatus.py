import sqlite3
import time
import random
import os
import serial

# Connect to SQLite database
db_path = os.path.join(os.path.dirname(__file__), '..', 'Database', 'elevator_system.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Simulate sensor data for testing
def simulate_sensor_data():
    return random.choice(["Occupied", "Available"])

# Function to get parking spot details
def get_parking_spot_details(spot_id):
    cursor.execute("SELECT Spot_ID, Spot_type, Level, Is_occupied FROM Parking_Spots WHERE Spot_ID = ?", (spot_id,))
    return cursor.fetchone()

# Function to update both Parking_Spots and Parking_Sensors tables
def update_parking_status(spot_id, sensor_id, sensor_status):
    # Update the Parking_Spots table
    is_occupied = 1 if sensor_status == "Occupied" else 0
    cursor.execute("UPDATE Parking_Spots SET Is_occupied = ? WHERE Spot_ID = ?", (is_occupied, spot_id))

    # Update the Parking_Sensors table
    cursor.execute('''
        INSERT INTO Parking_Sensors (Sensor_ID, Spot_ID, Status, Last_checked, Sensor_type)
        VALUES (?, ?, ?, datetime('now'), 'Ultrasonic')
        ON CONFLICT(Sensor_ID) DO UPDATE SET
            Status = excluded.Status,
            Last_checked = datetime('now')
    ''', (sensor_id, spot_id, sensor_status))

    # Commit changes
    conn.commit()

try:
    # Simulate data or receive from the serial
    while True:
        # Simulate data for testing
        sensor_data = simulate_sensor_data()
        print(f"Simulated Received: {sensor_data}")

        # Specify the spot and sensor IDs
        spot_id = 1  
        sensor_id = 1  

        # Update parking spot and sensor status in the database
        update_parking_status(spot_id, sensor_id, sensor_data)

        # Retrieve updated parking spot details
        details = get_parking_spot_details(spot_id)
        print(f"Updated Spot Details: ID={details[0]}, Type={details[1]}, Level={details[2]}, Occupied={'Yes' if details[3] else 'No'}")

        # Wait before the next reading
        time.sleep(2)

    # Real version for receiving data from Arduino
    ser = serial.Serial('COM3', 9600)
    while True:
        if ser.in_waiting > 0:
            sensor_data = ser.readline().decode('utf-8').strip()
            print(f"Received: {sensor_data}")

            # Assuming the sensor ID is 1 and spot ID is 1
            sensor_id = 1
            spot_id = 1

            # Update parking spot and sensor status in the database
            update_parking_status(spot_id, sensor_id, sensor_data)

finally:
    # Close the database connection
    conn.close()
    print("Database connection closed.")
