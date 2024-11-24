// Vertical motor pins
const int stepPins[4] = {6, 8, 10, 12}; // STEP pins for 4 motors
const int dirPins[4] = {7, 9, 11, 13};  // DIR pins for 4 motors

// Ultrasonic sensor pins
const int triggerPin = 2;  // Trigger pin
const int echoPin = 3;     // Echo pin

// Constants
const int stepsPerLevel = 2000;  // Steps to move between levels
const int sensorThreshold = 15; // Distance threshold in cm

// Status variables
bool carDetected = false;

void setup() {
  Serial.begin(9600);

  // Set motor pins as outputs
  for (int i = 0; i < 4; i++) {
    pinMode(stepPins[i], OUTPUT);
    pinMode(dirPins[i], OUTPUT);
  }

  // Set sensor pins
  pinMode(triggerPin, OUTPUT);
  pinMode(echoPin, INPUT);

  Serial.println("Vertical elevator system initialized");
}

// Function to move the vertical motors
void moveVertical(int steps) {
  bool direction = (steps > 0); // True for UP, False for DOWN
  steps = abs(steps);

  // Set direction for all motors
  for (int i = 0; i < 4; i++) {
    digitalWrite(dirPins[i], direction);
  }

  // Step all motors simultaneously
  for (int s = 0; s < steps; s++) {
    for (int i = 0; i < 4; i++) {
      digitalWrite(stepPins[i], HIGH);
    }
    delayMicroseconds(500); // Adjust delay for speed
    for (int i = 0; i < 4; i++) {
      digitalWrite(stepPins[i], LOW);
    }
    delayMicroseconds(500);
  }

  Serial.println("Movement complete");
}

// Function to check if a car is detected in the parking spot
int readSensorDistance() {
  // Send trigger pulse
  digitalWrite(triggerPin, LOW);
  delayMicroseconds(2);
  digitalWrite(triggerPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(triggerPin, LOW);

  // Measure the echo pulse duration
  long duration = pulseIn(echoPin, HIGH);
  int distance = duration * 0.034 / 2; // Convert to cm

  return distance;
}

// Function to process commands from Python
void processCommand(String command) {
  if (command.startsWith("MOVE_VERTICAL_UP")) {
    int steps = command.substring(17).toInt(); // Parse step count
    moveVertical(steps);
    Serial.println("Moved Up");
  } else if (command.startsWith("MOVE_VERTICAL_DOWN")) {
    int steps = command.substring(19).toInt(); // Parse step count
    moveVertical(-steps);
    Serial.println("Moved Down");
  } else if (command == "CHECK_SPOT") {
    int distance = readSensorDistance();
    if (distance < sensorThreshold) {
      Serial.println("Spot Occupied");
    } else {
      Serial.println("Spot Free");
    }
  } else {
    Serial.println("Invalid Command");
  }
}

void loop() {
  // Listen for commands from Python
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim(); // Remove whitespace
    processCommand(command);
  }
}
