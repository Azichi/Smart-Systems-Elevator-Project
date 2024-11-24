import serial
import sqlite3
import time
from datetime import datetime


# Serial port settings
SERIAL_PORT = 'COM3' 
BAUD_RATE = 9600

# Database file path
DB_PATH = 'C:\\Users\\Azi\\iCloudDrive\\School\\Year 3\\Term 1\\Smart Systems\\Database\\tests\\parking_system.db'

# Parking spot ID
PARKING_SPOT_ID = 1


try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2) 
    print(f"Connected to Arduino on port {SERIAL_PORT}")
except serial.SerialException as e:
    print(f"Error connecting to serial port {SERIAL_PORT}: {e}")
    exit(1)


try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    print(f"Connected to database at {DB_PATH}")
except sqlite3.Error as e:
    print(f"Error connecting to database: {e}")
    exit(1)


def update_parking_status(spot_id, is_occupied):
    try:
        cursor.execute("""
            UPDATE Parking_Spots
            SET Is_Occupied = ?
            WHERE Spot_ID = ?
        """, (is_occupied, spot_id))
        conn.commit()
        print(f"Updated Parking_Spots: Spot_ID={spot_id}, Is_Occupied={is_occupied}")
    except sqlite3.Error as e:
        print(f"Error updating parking status: {e}")

def log_parking_entry(spot_id):
    try:
        entry_time = datetime.now()
        cursor.execute("""
            INSERT INTO Parking_Receipts (Spot_ID, Entry_Time)
            VALUES (?, ?)
        """, (spot_id, entry_time))
        conn.commit()
        print(f"Logged parking entry: Spot_ID={spot_id}, Entry_Time={entry_time}")
    except sqlite3.Error as e:
        print(f"Error logging parking entry: {e}")

def log_parking_exit(spot_id):
    try:
        exit_time = datetime.now()
        cursor.execute("""
            UPDATE Parking_Receipts
            SET Exit_Time = ?
            WHERE Spot_ID = ? AND Exit_Time IS NULL
        """, (exit_time, spot_id))
        conn.commit()
        print(f"Logged parking exit: Spot_ID={spot_id}, Exit_Time={exit_time}")
    except sqlite3.Error as e:
        print(f"Error logging parking exit: {e}")


print("Starting main loop.")

try:
    while True:
        if ser.in_waiting > 0:
            arduino_message = ser.readline().decode('utf-8').strip()
            print(f"Received from Arduino: '{arduino_message}'")
            
            if arduino_message == "Parked":
                # Update parking spot status to occupied
                update_parking_status(PARKING_SPOT_ID, True)
                # Log the parking entry
                log_parking_entry(PARKING_SPOT_ID)
            elif arduino_message == "Retrieved":
                # Update parking spot status to available
                update_parking_status(PARKING_SPOT_ID, False)
                # Log the parking exit
                log_parking_exit(PARKING_SPOT_ID)
        else:
            # No data from Arduino
            time.sleep(0.1)
except KeyboardInterrupt:
    print("Exiting program.")
finally:
    # Close serial and database connections
    ser.close()
    conn.close()
    print("Closed serial and database connections.")
