import sqlite3
import time
from datetime import datetime
import random
import tkinter as tk
from tkinter import messagebox, simpledialog
import os 
import serial 

# Constants
steps_to_level_1 = 2000 
db_path = os.path.join(os.path.dirname(__file__), 'database', 'elevator_system.db')
arduino_port = 'COM3'
baud_rate = 9600
status_label = None

# Serial setup for Arduino communication
arduino = None
try:
    arduino = serial.Serial(arduino_port, baud_rate, timeout=1)
    print(f"Connected to Arduino on {arduino_port}")
except serial.SerialException as e:
    print(f"Failed to connect to Arduino: {e}")

# Database Functions
def setup_database():
    try:
        conn = sqlite3.connect(db_path)
        conn.close()
        print("Connected to database.")
    except sqlite3.Error as e:
        print(f"Failed to connect to the database: {e}")

def insert_parking_receipt(spot_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    entry_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    receipt_id = f"R{random.randint(1000, 9999)}"
    try:
        cursor.execute(
            "INSERT INTO Parking_Receipts (Receipt_ID, Entry_time, Spot_ID) VALUES (?, ?, ?)",
            (receipt_id, entry_time, spot_id)
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error inserting parking receipt: {e}")
        receipt_id = None
    finally:
        conn.close()
    if receipt_id:
        print(f"Inserted parking receipt for Spot_ID {spot_id}: {receipt_id}")
    return receipt_id

def validate_receipt(receipt_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT Spot_ID FROM Parking_Receipts WHERE Receipt_ID = ? AND Exit_time IS NULL",
            (receipt_id,)
        )
        result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        print(f"Error retrieving Spot_ID: {e}")
        return None
    finally:
        conn.close()

def update_exit_time(receipt_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    exit_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute(
            "UPDATE Parking_Receipts SET Exit_time = ? WHERE Receipt_ID = ?",
            (exit_time, receipt_id)
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error updating parking receipt: {e}")
    finally:
        conn.close()
    print(f"Updated parking receipt {receipt_id} with exit time")

# Function to update the status of a parking spot
def update_spot_status(spot_id, is_occupied):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE Parking_Spots
            SET Is_occupied = ?
            WHERE Spot_ID = ?
        """, (is_occupied, spot_id))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error updating spot status: {e}")
    finally:
        conn.close()
    status = "occupied" if is_occupied else "available"
    print(f"Spot {spot_id} marked as {status}")

# Arduino Movement Functions
def send_command(command):
    if arduino:
        try:
            arduino.write((command + '\n').encode())
            response = arduino.readline().decode().strip()
            print(f"Arduino response: {response}")
            return response
        except Exception as e:
            print(f"Error sending command: {e}")
    else:
        print("Arduino connection not established.")
    return None

def move_to_ground_level():
    send_command("MOVE_VERTICAL_DOWN TO GROUND")
    print("Moved to ground level.")

def move_to_level_1():
    send_command(f"MOVE_VERTICAL_UP {steps_to_level_1}")
    print("Moved to Level 1.")

def check_parking_spot():
    response = send_command("CHECK_SPOT")
    if response == "Spot Occupied":
        print("Level 1 is occupied.")
        return True
    elif response == "Spot Free":
        print("Level 1 is available.")
        return False
    else:
        print("Error checking occupancy.")
        return None

# Park and Retrieve Functions
def park_car():
    if check_parking_spot():
        messagebox.showerror("Error", "Level 1 is occupied. Cannot park.")
        return
    move_to_level_1()
    spot_id = 1  # Assuming Spot_ID=1 corresponds to Level 1
    receipt_id = insert_parking_receipt(spot_id)
    if receipt_id:
        messagebox.showinfo("Receipt", f"Your parking receipt ID is: {receipt_id}")
        print(f"Car parked at Spot_ID {spot_id}. Receipt ID: {receipt_id}")
        # Update Parking_Spots table to set Is_occupied = True
        update_spot_status(spot_id, True)
    else:
        messagebox.showerror("Error", "Failed to generate parking receipt.")

def retrieve_car():
    receipt_id = simpledialog.askstring("Input", "Enter your receipt ID:")
    if receipt_id:
        spot_id = validate_receipt(receipt_id)
        if spot_id:
            move_to_ground_level()
            update_exit_time(receipt_id)
            messagebox.showinfo("Success", "Your car has been retrieved.")
            print(f"Car retrieved from Spot_ID {spot_id} with Receipt ID: {receipt_id}")
            # Update Parking_Spots table to set Is_occupied = False
            update_spot_status(spot_id, False)
        else:
            messagebox.showerror("Error", "Invalid receipt ID or car already retrieved.")
    else:
        messagebox.showerror("Error", "No receipt ID entered.")

def update_status():
    status = check_parking_spot()
    if status is True:
        status_label.config(text="Status: Occupied", fg="red")
    elif status is False:
        status_label.config(text="Status: Available", fg="green")
    else:
        status_label.config(text="Status: Error Checking", fg="orange")
    status_label.after(3000, update_status)

# GUI Setup
def setup_gui():
    global status_label
    root = tk.Tk()
    root.title("Elevator System")
    root.geometry("800x600")

    tk.Label(root, text="Welcome to the Parking System", font=("Helvetica", 16)).pack(pady=10)

    button_frame = tk.Frame(root)
    button_frame.pack(side="top", pady=10)

    # Consistent Button Styling
    button_style = {
        "font": ("Helvetica", 12),
        "bg": "lightblue",
        "fg": "black",
        "padx": 10,
        "pady": 10,
        "width": 20
    }

    # Park Your Car Button
    park_button = tk.Button(
        button_frame, 
        text="Park Your Car", 
        command=park_car, 
        **button_style
    )
    park_button.pack(side="left", padx=5)

    # Retrieve Your Car Button
    retrieve_button = tk.Button(
        button_frame, 
        text="Retrieve Your Car", 
        command=retrieve_car, 
        **button_style
    )
    retrieve_button.pack(side="left", padx=5)

    # Status Label
    status_label = tk.Label(root, text="Checking status...", font=("Helvetica", 14), fg="blue")
    status_label.pack(pady=10)

    # Start status updates
    update_status()

    root.mainloop()

# Main Execution
if __name__ == "__main__":
    try:
        setup_database()
        setup_gui()
    except Exception as e:
        print(f"An error occurred during startup: {e}")
        import traceback
        traceback.print_exc()
