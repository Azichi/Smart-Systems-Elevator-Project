import sqlite3
import time
from datetime import datetime
import serial
import tkinter as tk
from tkinter import messagebox
import os

# Constants for physical dimensions
level_height_cm = 20  # Height between levels in cm
platform_width = 20    # Width of the platform in pixels
elevator_shaft_x = 150  # X position of the elevator shaft in pixels
cm_to_steps = 10       # Conversion factor from cm to steps

# Database connection
db_path = os.path.join(os.path.dirname(__file__), 'database', 'elevator_system.db')

# Arduino port setup
arduino_port = 'COM3'
baud_rate = 9600
arduino = None

# Initialize serial connection
try:
    arduino = serial.Serial(arduino_port, baud_rate, timeout=1)
    print(f"Connected to Arduino on {arduino_port}")
except serial.SerialException as e:
    print(f"Failed to connect to Arduino: {e}")

time.sleep(2)  # Wait for connection

def connect_db():
    try:
        conn = sqlite3.connect(db_path)
        return conn
    except sqlite3.Error as e:
        print(f"Failed to connect to the database: {e}")
        return None

def setup_database():
    try:
        conn = sqlite3.connect(db_path)
        conn.close()
        print("Connected to database.")
    except sqlite3.Error as e:
        print(f"Failed to connect to the database: {e}")

def populate_parking_spots():
    conn = connect_db()
    if conn is None:
        return
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM Parking_Spots")
        count = cursor.fetchone()[0]
        if count == 0:
            parking_spots = []
            sensor_id = 201  # Starting Sensor_ID, adjust as necessary
            for level in range(1, 7):
                spot_id_left = level * 2 - 1
                spot_id_right = level * 2
                parking_spots.append((spot_id_left, level, 'left', False, True, sensor_id))
                parking_spots.append((spot_id_right, level, 'right', False, True, sensor_id + 1))
                sensor_id += 2  # Increment Sensor_ID for next spot
            cursor.executemany("""
                INSERT INTO Parking_Spots (Spot_ID, Level_ID, Spot_type, Is_occupied, Is_operational, Sensor_ID)
                VALUES (?, ?, ?, ?, ?, ?)
            """, parking_spots)
            conn.commit()
            print("Parking spots populated.")
    except sqlite3.Error as e:
        print(f"Error populating parking spots: {e}")
    finally:
        conn.close()

def send_command(command):
    if arduino:
        try:
            arduino.write((command + '\n').encode())
            time.sleep(0.1)
            response = arduino.readline().decode().strip()
            print(f"Arduino response: {response}")
            return response
        except Exception as e:
            print(f"Failed to send command to Arduino: {e}")
            return None
    else:
        print("Arduino not connected.")
        return None

def move_platform(spot_id, action):
    conn = connect_db()
    if conn is None:
        return
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT Level_ID, Spot_type
            FROM Parking_Spots
            WHERE Spot_ID = ?
        """, (spot_id,))
        result = cursor.fetchone()
        if result:
            level_id, spot_type = result
            original_x = elevator_shaft_x
            original_y = level_id * level_height_cm
            target_x = elevator_shaft_x
            ground_y = 0

            vertical_distance_cm = abs(original_y - ground_y)
            steps = int(vertical_distance_cm * cm_to_steps)

            if original_y > ground_y:
                send_command(f"MOVE_VERTICAL_DOWN {steps}")
            else:
                send_command(f"MOVE_VERTICAL_UP {steps}")

            if spot_type.lower() == 'left':
                send_command(f"MOVE_HORIZONTAL_LEFT {steps_to_middle_position}")
            else:
                send_command(f"MOVE_HORIZONTAL_RIGHT {steps_to_middle_position}")

            if action == 'park':
                print("Car is being parked.")
                # Update Parking_Spots to set Is_occupied = True
                cursor.execute("""
                    UPDATE Parking_Spots
                    SET Is_occupied = 1
                    WHERE Spot_ID = ?
                """, (spot_id,))
                conn.commit()
                print(f"Parking spot {spot_id} marked as occupied.")
            elif action == 'retrieve':
                print("Car is being retrieved.")
                # Update Parking_Spots to set Is_occupied = False
                cursor.execute("""
                    UPDATE Parking_Spots
                    SET Is_occupied = 0
                    WHERE Spot_ID = ?
                """, (spot_id,))
                conn.commit()
                print(f"Parking spot {spot_id} marked as available.")
    except sqlite3.Error as e:
        print(f"Error moving platform: {e}")
    finally:
        conn.close()

# Main
if __name__ == "__main__":
    print("Initializing system...")
    setup_database()
    populate_parking_spots()
    print("System initialized.")
