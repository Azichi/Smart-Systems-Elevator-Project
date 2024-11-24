import serial
import time

# Serial setup for Arduino communication
arduino_port = 'COM3' 
baud_rate = 9600
try:
    arduino = serial.Serial(arduino_port, baud_rate, timeout=1)
    print(f"Connected to Arduino on {arduino_port}")
except serial.SerialException as e:
    print(f"Failed to connect to Arduino: {e}")
    arduino = None

time.sleep(2)  # Wait for connection

# Test Type: 'horizontal' | 'vertical'
test_type = 'horizontal'  

class MotorTest:
    def __init__(self, test_type):
        self.test_type = test_type

    def send_command(self, command):
        if arduino:
            try:
                arduino.write((command + '\n').encode())
                print(f"Sent command: {command}")
                
                if arduino.in_waiting > 0:
                    response = arduino.readline().decode().strip()
                    print(f"Arduino response: {response}")
            except Exception as e:
                print(f"Error sending command: {e}")
        else:
            print("Arduino connection not established.")

    def run_test(self):
        if self.test_type == 'horizontal':
            print("Testing horizontal motor...") 
            self.send_command("MOVE_HORIZONTAL_TO_ELEVATOR")
            time.sleep(2)  
            self.send_command("MOVE_HORIZONTAL_TO_SPOT")
        elif self.test_type == 'vertical':
            print("Testing vertical motor...") 
            self.send_command("MOVE_VERTICAL_DOWN")
            time.sleep(2)  
            self.send_command("MOVE_VERTICAL_UP")
        else:
            print("Invalid test type specified.")

# Create an instance of MotorTest based on test type
motor_test_instance = MotorTest(test_type)
motor_test_instance.run_test()
