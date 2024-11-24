import sqlite3
import time
import tkinter as tk
import os
import random
from datetime import datetime
from tkinter import messagebox

# Database connection
db_path = os.path.join(os.path.dirname(__file__), 'database', 'elevator_system.db')

# Movement steps for different stages
steps_above_level_1 = 2700
steps_to_middle_position = -1000
steps_to_level_1 = -200
steps_to_original_position = 1000
steps_to_ground_level = -2500

# Mock Arduino class for simulation
class MockArduino:
    def __init__(self):
        self.vertical_position = 0
        self.horizontal_position_left = 0
        self.horizontal_position_right = 0
        print("Mock Arduino initialized.")

    def write(self, command):
        try:
            command = command.decode().strip()
            parts = command.split()
            if not parts:
                print("No command received.")
                return

            motor_command = parts[0]
            steps = int(parts[1]) if len(parts) > 1 else None

            if motor_command == 'LOAD_CAR':
                print("Car Loaded.")

            elif motor_command == 'MOVE_VERTICAL_UP' and steps is not None:
                self.vertical_position += steps
                print(f"Elevator moved up by {steps} steps to position {self.vertical_position}.")

            elif motor_command == 'MOVE_VERTICAL_DOWN' and steps is not None:
                self.vertical_position -= steps
                print(f"Elevator moved down by {steps} steps to position {self.vertical_position}.")

            elif motor_command == 'MOVE_HORIZONTAL_LEFT' and steps is not None:
                self.horizontal_position_left += steps
                print(f"Left horizontal motor moved by {steps} steps to position {self.horizontal_position_left}.")

            elif motor_command == 'MOVE_HORIZONTAL_RIGHT' and steps is not None:
                self.horizontal_position_right += steps
                print(f"Right horizontal motor moved by {steps} steps to position {self.horizontal_position_right}.")

            elif motor_command == 'CHECK_SPOT':
                print("Spot Free.")

            else:
                print(f"Unknown command: {motor_command}")

        except Exception as e:
            print(f"Error in MockArduino.write: {e}")

    def readline(self):
        # Simulate response from Arduino
        time.sleep(0.5)
        if random.choice([True, False]):
            return b"Car in Spot\n"
        else:
            return b"Car not in Spot\n"

# GUI
class ParkingSimulatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Elevator System Mock Simulator")
        self.arduino = MockArduino()

        
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

        print("Connected to SQLite database at:", db_path)
        self.setup_database()

    def setup_database(self):
        try:
            conn = sqlite3.connect(db_path)
            conn.close()
            print("Connected to database.")
        except sqlite3.Error as e:
            print(f"Failed to connect to the database: {e}")

    def send_command(self, command, steps=None):
        if self.arduino:
            try:
                if steps is not None:
                    full_command = f"{command} {steps}\n"
                else:
                    full_command = f"{command}\n"
                self.arduino.write(full_command.encode())
                print(f"Sent command: {full_command.strip()}")
                time.sleep(1) 
                response = self.arduino.readline().decode().strip()
                print(f"Arduino response: {response}")
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
        if response == "Car in Spot":
            print("Parking spot is occupied. Aborting.")
            messagebox.showwarning("Parking Spot", "Parking spot is occupied. Aborting.")
            return

        print("Parking spot is free. Proceeding with parking.")

        # Parking sequence
        self.send_command("LOAD_CAR")
        time.sleep(1)
        self.send_command("MOVE_VERTICAL_UP", steps_above_level_1)
        self.send_command("MOVE_HORIZONTAL_LEFT", steps_to_middle_position)
        self.send_command("MOVE_VERTICAL_DOWN", steps_to_level_1)

        # Update parking spot status in database
        spot_id = 1  
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Parking_Spots (Spot_ID, Level_ID, Spot_type, Is_occupied, Is_operational, Sensor_ID)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(Spot_ID) DO UPDATE SET Is_occupied=1
            """, (spot_id, 1, 'left', True, True, 201)) 
            conn.commit()
            print(f"Updated Parking_Spots for Spot_ID {spot_id} to occupied.")
        except sqlite3.Error as e:
            print(f"Error updating Parking_Spots: {e}")
            messagebox.showerror("Database Error", "Failed to update parking spot status.")
        finally:
            conn.close()

        # Complete parking sequence
        self.send_command("MOVE_HORIZONTAL_RIGHT", steps_to_original_position)
        self.send_command("MOVE_VERTICAL_DOWN", steps_to_ground_level)

        # Log parking action in Parking_Receipts
        receipt_id = self.generate_receipt_id()
        entry_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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

        print("Car parked successfully.")

    def on_close(self):
        print("Application closed.")
        self.root.destroy()

# Main
if __name__ == "__main__":
    root = tk.Tk()
    app = ParkingSimulatorApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
