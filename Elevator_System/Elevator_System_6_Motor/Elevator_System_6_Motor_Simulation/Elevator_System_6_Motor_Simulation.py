import sqlite3
import time
from datetime import datetime
import random
import tkinter as tk
from tkinter import messagebox
import os

# Constants for physical dimensions
level_height_cm = 20    # Height between levels in cm
platform_width = 20     # Width of the platform in pixels
elevator_shaft_x = 150  # X position of the elevator shaft in pixels

# Mapping from cm to pixels for the simulation
cm_to_px = 5 

# Global variables
platforms = {}
root = None
canvas = None

# Database connection
db_path = os.path.join(os.path.dirname(__file__), 'database', 'elevator_system.db')


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
        # Check if Parking_Spots table is empty
        cursor.execute("SELECT COUNT(*) FROM Parking_Spots")
        count = cursor.fetchone()[0]
        if count == 0:
            # Insert initial data into Parking_Spots
            parking_spots = []
            sensor_id = 201  
            for level in range(1, 7):  # Levels 1 to 6
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

# Function to insert a parking receipt
def insert_parking_receipt(spot_id):
    conn = connect_db()
    if conn is None:
        return None
    cursor = conn.cursor()
    entry_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    receipt_id = f"R{random.randint(1000, 9999)}"
    try:
        cursor.execute("""
            INSERT INTO Parking_Receipts (Receipt_ID, Entry_time, Spot_ID)
            VALUES (?, ?, ?)
        """, (receipt_id, entry_time, spot_id))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error inserting parking receipt: {e}")
        receipt_id = None
    finally:
        conn.close()
    if receipt_id:
        print(f"Inserted parking receipt for Spot_ID {spot_id}: {receipt_id}")
    return receipt_id

# Function to update a parking receipt with exit time
def update_exit_time(receipt_id):
    conn = connect_db()
    if conn is None:
        return
    cursor = conn.cursor()
    exit_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute("""
            UPDATE Parking_Receipts
            SET Exit_time = ?
            WHERE Receipt_ID = ?
        """, (exit_time, receipt_id))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error updating parking receipt: {e}")
    finally:
        conn.close()
    print(f"Updated parking receipt {receipt_id} with exit time")

# Function to find the closest available platform
def find_available_platform():
    conn = connect_db()
    if conn is None:
        return None
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT Spot_ID, Level_ID, Spot_type
            FROM Parking_Spots
            WHERE Is_occupied = 0 AND Is_operational = 1
            ORDER BY ABS(Level_ID - 1), Spot_ID
            LIMIT 1
        """)
        result = cursor.fetchone()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        result = None
    finally:
        conn.close()
    if result:
        spot_id, level_id, spot_type = result
        return spot_id, level_id, spot_type
    else:
        return None

# Function to update the status of a parking spot
def update_spot_status(spot_id, is_occupied):
    conn = connect_db()
    if conn is None:
        return
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

    # Update graphical representation
    platform = platforms.get(spot_id)
    if platform and canvas:
        color = 'red' if is_occupied else 'green'
        canvas.itemconfig(platform['rect'], fill=color)

# Function to validate receipt and get Spot_ID
def validate_receipt(receipt_id):
    conn = connect_db()
    if conn is None:
        return None
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT Spot_ID FROM Parking_Receipts
            WHERE Receipt_ID = ? AND Exit_time IS NULL
        """, (receipt_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        print(f"Error retrieving Spot_ID: {e}")
        return None
    finally:
        conn.close()

# Function to move the platform to pick up or drop off the car
def move_platform(spot_id, action):
    global canvas, platforms
    platform = platforms.get(spot_id)
    if not platform:
        print(f"No platform found for Spot_ID {spot_id}")
        return


    canvas_width = canvas.winfo_width()
    canvas_height = canvas.winfo_height()

    # Constants for platform and shaft dimensions
    platform_width_px = level_height_cm * cm_to_px
    platform_height_px = platform_width_px / 4
    shaft_center_x = canvas_width // 2  # Exact center of the shaft
    ground_y = canvas_height - platform_height_px  # Ground level for the platform

    # Current platform position
    original_x = platform['x']
    original_y = platform['y']

    print(f"Original Position - Spot_ID: {spot_id}, X: {original_x}, Y: {original_y}")
    print(f"Shaft Center X: {shaft_center_x}, Ground Y: {ground_y}")

    # Step 1: Horizontal movement to align with shaft center
    dx = 1 if original_x < shaft_center_x else -1
    while abs(platform['x'] - shaft_center_x) > 1:
        platform['x'] += dx
        canvas.move(platform['rect'], dx, 0)
        canvas.update()
        time.sleep(0.005)

    # Snap to exact alignment with shaft center
    canvas.move(platform['rect'], shaft_center_x - platform['x'], 0)
    platform['x'] = shaft_center_x

    print(f"Aligned with Shaft - Spot_ID: {spot_id}, X: {platform['x']}")

    # Step 2: Vertical movement down to ground level
    dy = 1
    while platform['y'] < ground_y: 
        platform['y'] += dy
        canvas.move(platform['rect'], 0, dy)
        canvas.update()
        time.sleep(0.005)

    # Snap to exact ground level
    canvas.move(platform['rect'], 0, ground_y - platform['y'])
    platform['y'] = ground_y

    print(f"Moved to Ground - Spot_ID: {spot_id}, Y: {platform['y']}")

    # Simulate loading/unloading
    if action == 'park':
        print(f"Car is being loaded onto Spot_ID: {spot_id}...")
    elif action == 'retrieve':
        print(f"Car is being unloaded from Spot_ID: {spot_id}...")
    time.sleep(1)

    # Step 3: Vertical movement back up to original position
    while platform['y'] > original_y:  
        platform['y'] -= dy
        canvas.move(platform['rect'], 0, -dy)
        canvas.update()
        time.sleep(0.005)

    
    canvas.move(platform['rect'], 0, original_y - platform['y'])
    platform['y'] = original_y

    print(f"Returned to Original Height - Spot_ID: {spot_id}, Y: {platform['y']}")

    # Step 4: Horizontal movement back to original position
    dx = 1 if platform['x'] < original_x else -1
    while abs(platform['x'] - original_x) > 1: 
        platform['x'] += dx
        canvas.move(platform['rect'], dx, 0)
        canvas.update()
        time.sleep(0.005)

    
    canvas.move(platform['rect'], original_x - platform['x'], 0)
    platform['x'] = original_x

    print(f"Returned to Original Position - Spot_ID: {spot_id}, X: {platform['x']}")

def clear_all_parking_spots():
    conn = connect_db()
    if conn is None:
        return
    cursor = conn.cursor()
    try:
        # Reset all parking spots to available
        cursor.execute("UPDATE Parking_Spots SET Is_occupied = 0")
        
        # Clear all receipts
        cursor.execute("DELETE FROM Parking_Receipts")
        
        conn.commit()

        # Update the canvas
        for spot_id, platform in platforms.items():
            canvas.itemconfig(platform['rect'], fill='green') 
        
        print("All parking spots cleared, and all receipt records deleted.")
        messagebox.showinfo("Clear All", "All parking spots have been cleared and receipts deleted.")
    except sqlite3.Error as e:
        print(f"Error clearing parking spots and receipts: {e}")
    finally:
        conn.close()

# Function for the graphical simulation
def initialize_simulation(frame):
    global canvas, platforms
    platforms = {}  

    frame.update_idletasks()

    # Set canvas dimensions
    canvas_width = 1920 
    canvas_height = 800  
    canvas = tk.Canvas(frame, width=canvas_width, height=canvas_height, bg='white')
    canvas.pack(fill='both', expand=True)

    conn = connect_db()
    if conn is None:
        return
    cursor = conn.cursor()

    try:
        # Check parking spots
        cursor.execute("""
            SELECT Spot_ID, Level_ID, Spot_type, Is_occupied
            FROM Parking_Spots
        """)
        spots_data = cursor.fetchall()

        # Define platform and shaft dimensions
        platform_width_px = level_height_cm * cm_to_px
        platform_height_px = platform_width_px / 4
        shaft_center = canvas_width // 2 

        # Calculate left and right platform positions relative to the shaft
        left_block_center = shaft_center - platform_width_px
        right_block_center = shaft_center + platform_width_px

        # Draw the elevator shaft first
        canvas.create_rectangle(
            shaft_center - platform_width_px / 2, 100,
            shaft_center + platform_width_px / 2, canvas_height + 50,
            fill='black', outline='black'
        )

        # Draw the platforms after the shaft
        for spot in spots_data:
            spot_id, level_id, spot_type, is_occupied = spot
            y = canvas_height - (level_id * level_height_cm * cm_to_px) 

            if spot_type.lower() == 'left':
                x = left_block_center
            elif spot_type.lower() == 'right':
                x = right_block_center
            else:
                continue

            color = 'red' if is_occupied else 'green'

            # Draw each platform rectangle
            rect = canvas.create_rectangle(
                x - platform_width_px / 2, y - platform_height_px / 2,
                x + platform_width_px / 2, y + platform_height_px / 2,
                fill=color, outline='black'
            )
            platforms[spot_id] = {'rect': rect, 'x': x, 'y': y}

        # Draw the tower boundary (structure rectangle)
        tower_margin = 5  
        canvas.create_rectangle(
            left_block_center - platform_width_px / 2,  
            tower_margin + 100,                         
            right_block_center + platform_width_px / 2,  
            canvas_height + 50,                          
            outline='black', width=10  
        )

    except sqlite3.Error as e:
        print(f"Error initializing simulation: {e}")
    finally:
        conn.close()

# Function to print the parking overview
def print_parking_overview():
    conn = connect_db()
    if conn is None:
        return
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT ps.Level_ID, ps.Spot_ID, ps.Spot_type, ps.Is_occupied, pr.Receipt_ID
            FROM Parking_Spots ps
            LEFT JOIN Parking_Receipts pr ON ps.Spot_ID = pr.Spot_ID AND pr.Exit_time IS NULL
            ORDER BY ps.Level_ID, ps.Spot_ID
        """)
        data = cursor.fetchall()

        
        print("\nParking Overview:")
        print(f"{'Level':<8}{'Spot_ID':<10}{'Side':<10}{'Occupied':<12}{'Receipt_ID':<15}")
        print("-" * 55) 

        for row in data:
            level_id, spot_id, spot_type, is_occupied, receipt_id = row
            occupied_text = 'Yes' if is_occupied else 'No'
            receipt_id_text = receipt_id if receipt_id else 'N/A'
            
            print(f"{level_id:<8}{spot_id:<10}{spot_type:<10}{occupied_text:<12}{receipt_id_text:<15}")
    except sqlite3.Error as e:
        print(f"Error printing parking overview: {e}")
    finally:
        conn.close()

# GUI for the main menu
def welcome_screen():
    global root, canvas, platforms

    root = tk.Tk()
    root.title("Smart Parking System")
    root.geometry("800x600")

    main_frame = tk.Frame(root)
    main_frame.pack(fill='both', expand=True)

    control_frame = tk.Frame(main_frame)
    control_frame.pack(side='top', fill='x', pady=10)

    label = tk.Label(control_frame, text="Welcome to our Smart Parking System", font=("Arial", 24))
    label.pack(pady=10)

    button_frame = tk.Frame(control_frame)
    button_frame.pack(pady=10)

    
    park_button = tk.Button(
        button_frame, 
        text="Park Your Car", 
        command=park_car, 
        font=("Helvetica", 12), 
        bg="lightblue", 
        fg="black", 
        padx=10, 
        pady=10,
        width=20
    )
    park_button.pack(side='left', padx=20)

    
    retrieve_button = tk.Button(
        button_frame, 
        text="Retrieve Your Car", 
        command=retrieve_car_screen, 
        font=("Helvetica", 12), 
        bg="lightblue", 
        fg="black", 
        padx=10, 
        pady=10,
        width=20
    )
    retrieve_button.pack(side='left', padx=20)

    
    clear_button = tk.Button(
        button_frame, 
        text="Clear All Parking Spots", 
        command=clear_all_parking_spots, 
        font=("Helvetica", 12), 
        bg="lightblue", 
        fg="black", 
        padx=10, 
        pady=10,
        width=20
    )
    clear_button.pack(side='left', padx=20)

    simulation_frame = tk.Frame(main_frame)
    simulation_frame.pack(fill='both', expand=True, pady=10)

    # Initialize the simulation
    initialize_simulation(simulation_frame)

    root.mainloop()

# Function for parking a car
def park_car():
    result = find_available_platform()
    if result:
        spot_id, level_id, spot_type = result
        # Move platform to pick up the car
        move_platform(spot_id, 'park')
        # Mark spot as occupied
        update_spot_status(spot_id, True)
        # Generate receipt
        receipt_id = insert_parking_receipt(spot_id)
        if receipt_id:
            print(f"Your parking receipt ID is: {receipt_id}")
            messagebox.showinfo("Receipt", f"Your parking receipt ID is: {receipt_id}")
        else:
            messagebox.showerror("Error", "Failed to generate parking receipt.")
    else:
        messagebox.showinfo("No Available Spots", "No available spots. Please try again later.")
    # Print parking overview
    print_parking_overview()

# Function to display the retrieve car screen
def retrieve_car_screen():
    retrieve_window = tk.Toplevel(root)
    retrieve_window.title("Retrieve Car")
    retrieve_window.geometry("400x200")

    frame = tk.Frame(retrieve_window)
    frame.pack(pady=20)

    label = tk.Label(frame, text="Enter Receipt ID to Retrieve Your Car:", font=("Arial", 14))
    label.pack(pady=10)

    receipt_entry = tk.Entry(frame, font=("Arial", 14))
    receipt_entry.pack(pady=10)

    def retrieve_action():
        receipt_id = receipt_entry.get().strip()
        retrieve_window.destroy()
        retrieve_car(receipt_id)

 
    retrieve_button = tk.Button(
        frame, 
        text="Retrieve", 
        command=retrieve_action, 
        font=("Helvetica", 12), 
        bg="lightblue", 
        fg="black", 
        padx=10, 
        pady=10,
        width=20
    )
    retrieve_button.pack(pady=10)

# Function to retrieve a car
def retrieve_car(receipt_id):
    spot_id = validate_receipt(receipt_id)
    if spot_id:
        # Move platform to drop off the car
        move_platform(spot_id, 'retrieve')
        # Mark spot as available
        update_spot_status(spot_id, False)
        # Update receipt
        update_exit_time(receipt_id)
        # Notify user
        messagebox.showinfo("Car Retrieved", "Your car has been retrieved and is ready for pickup.")
    else:
        messagebox.showerror("Error", f"No active parking receipt found for Receipt ID {receipt_id}")
    # Print parking overview
    print_parking_overview()

if __name__ == "__main__":
    try:
        setup_database()
        populate_parking_spots()
        print_parking_overview()  # Initial parking overview
        welcome_screen()
    except Exception as e:
        print(f"An error occurred during startup: {e}")
        import traceback
        traceback.print_exc()
