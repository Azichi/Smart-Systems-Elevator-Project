import sqlite3
import time
import serial
import tkinter as tk
import os
import random
from datetime import datetime
from tkinter import messagebox

# Database connection
db_path = os.path.join(os.path.dirname(__file__), 'database', 'elevator_system.db')

# Movement steps for different stages
steps_above_level_1 = 2700  # Move slightly above level 1
steps_to_middle_position = -1000    # Move left horizontal motor to middle position
steps_to_level_1 = -200     # Move elevator down to level 1
steps_to_original_position = 1000  # Move right horizontal motor back
steps_to_ground_level = -2500  # Move elevator back down to ground level

# Serial setup for Arduino communication
arduino_port = 'COM3' 
baud_rate = 9600
try:
    arduino = serial.Serial(arduino_port, baud_rate, timeout=1)
    print(f"Connected to Arduino on {arduino_port}")
except serial.SerialException as e:
    print(f"Failed to connect to Arduino: {e}")
    arduino = None

time.sleep(2)

class ParkingSimulatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Elevator System Simulator")

       
        self.start_button = tk.Button(
            self.root, 
            text="Park Your Car", 
            command=self.park_car, 
            font=("Helvetica", 12), 
            bg="lightblue", 
            fg="black", 
            padx=10, 
            pady=10,
            width=20
        )
        self.start_button.pack(side="top", pady=10)

        print(f"Connected to SQLite database and Arduino at port {arduino_port}")
        self.setup_database()

    def setup_database(self):
        try:
            conn = sqlite3.connect(db_path)
            conn.close()
            print("Connected to database.")
        except sqlite3.Error as e:
            print(f"Failed to connect to the database: {e}")

    def send_command(self, command, steps=None):
        if arduino:
            try:
                if steps is not None:
                    full_command = f"{command} {steps}\n"
                else:
                    full_command = f"{command}\n"
                arduino.write(full_command.encode())
                print(f"Sent command: {full_command.strip()}")
                while True:
                    if arduino.in_waiting > 0:
                        response = arduino.readline().decode().strip()
                        print(f"Arduino response: {response}")
                        if response == "DONE":
                            break
                return response
            except Exception as e:
                print(f"Error sending command: {e}")
                return None
        else:
            print("Arduino not connected.")
            return None

    def generate_receipt_id(self):
        return f"R{random.randint(1000, 9999)}"

    def park_car(self):
        print("Starting park sequence...")

        # Check if the parking spot is free
        response = self.send_command("CHECK_SPOT")
        if response == "Spot Occupied":
            print("Parking spot is occupied. Aborting.")
            messagebox.showwarning("Parking Spot", "Parking spot is occupied. Aborting.")
            return

        print("Parking spot is free. Proceeding with parking.")

        # Load car
        self.send_command("LOAD_CAR")
        time.sleep(1)

        # Move elevator slightly above level 1
        self.send_command("MOVE_VERTICAL_UP", steps_above_level_1)

        # Move left horizontal motor to the middle position
        self.send_command("MOVE_HORIZONTAL_LEFT", steps_to_middle_position)

        # Move elevator down to level 1
        self.send_command("MOVE_VERTICAL_DOWN", steps_to_level_1)

        # Wait for "Car in Spot" signal
        self.monitor_car_in_spot()

        # Move right horizontal motor back to position
        self.send_command("MOVE_HORIZONTAL_RIGHT", steps_to_original_position)

        # Move elevator back down to ground level
        self.send_command("MOVE_VERTICAL_DOWN", steps_to_ground_level)

        # Log to Parking_Receipts table
        receipt_id = self.generate_receipt_id()
        entry_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        spot_id = 1 

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Parking_Receipts (Receipt_ID, Entry_time, Spot_ID)
                VALUES (?, ?, ?)
            """, (receipt_id, entry_time, spot_id))
            conn.commit()
            print(f"Inserted parking receipt: {receipt_id}")
            messagebox.showinfo("Parking Successful", f"Your Receipt ID is: {receipt_id}")
        except sqlite3.Error as e:
            print(f"Error inserting parking receipt: {e}")
            messagebox.showerror("Database Error", "Failed to log parking receipt.")
        finally:
            conn.close()

        # Update Parking_Spots table to set Is_occupied = True
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE Parking_Spots
                SET Is_occupied = 1
                WHERE Spot_ID = ?
            """, (spot_id,))
            conn.commit()
            print(f"Updated Parking_Spots for Spot_ID {spot_id} to occupied.")
        except sqlite3.Error as e:
            print(f"Error updating Parking_Spots: {e}")
            messagebox.showerror("Database Error", "Failed to update parking spot status.")
        finally:
            conn.close()

        print("Car parked successfully.")

    def monitor_car_in_spot(self):
        print("Monitoring for car arrival in the parking spot...")
        while True:
            if arduino:
                response = arduino.readline().decode().strip()
                if response == "Car in Spot":
                    print("Car detected in the parking spot.")

                    # Update the Parking_Spots table to set Is_occupied = True
                    spot_id = 1
                    try:
                        conn = sqlite3.connect(db_path)
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE Parking_Spots
                            SET Is_occupied = 1
                            WHERE Spot_ID = ?
                        """, (spot_id,))
                        conn.commit()
                        print("Parking spot updated to 'occupied' in the database.")
                        messagebox.showinfo("Parking Confirmed", "Car detected and spot marked as occupied.")
                    except sqlite3.Error as e:
                        print(f"Error updating Parking_Spots: {e}")
                        messagebox.showerror("Database Error", "Failed to update parking spot status.")
                    finally:
                        conn.close()
                    break
            else:
                print("Arduino not connected.")
                break

    def on_close(self):
        if arduino:
            arduino.close()
            print("Arduino connection closed.")
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ParkingSimulatorApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
