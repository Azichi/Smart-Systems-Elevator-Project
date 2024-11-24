// STEP and DIR pins for each motor
const int vertStepPin = 6;    // STEP pin for vertical motor
const int vertDirPin = 7;     // DIR pin for vertical motor
const int leftStepPin = 8;    // STEP pin for left horizontal motor
const int leftDirPin = 9;     // DIR pin for left horizontal motor
const int rightStepPin = 12;  // STEP pin for right horizontal motor
const int rightDirPin = 13;   // DIR pin for right horizontal motor

// Ultrasonic sensor pins
const int triggerPin = 10;    // Trigger pin for ultrasonic sensor
const int echoPin = 11;       // Echo pin for ultrasonic sensor

// Constants
const int stepsPerLevel = 2000;      // Steps to move between ground and level 1
const int sensorThreshold = 15;      // Distance threshold in cm to detect occupancy
const int horizontalStepsToElevator = 1000;  // Steps to move horizontal motor to elevator position
const int horizontalStepsToSpot = 1000;      // Steps to move horizontal motor to parking spot
const int verticalStepsDown = 2000;          // Steps to move vertical motor down
const int verticalStepsUp = 2000;            // Steps to move vertical motor up

// Variable to track car detection
bool carDetected = false;

void setup() {
  Serial.begin(9600);
  
  // Initialize motor pins as outputs
  pinMode(vertStepPin, OUTPUT);
  pinMode(vertDirPin, OUTPUT);
  pinMode(leftStepPin, OUTPUT);
  pinMode(leftDirPin, OUTPUT);
  pinMode(rightStepPin, OUTPUT);
  pinMode(rightDirPin, OUTPUT);
  
  // Initialize ultrasonic sensor pins
  pinMode(triggerPin, OUTPUT);
  pinMode(echoPin, INPUT);
  
  Serial.println("Elevator system initialized");
}

void moveMotor(int stepPin, int dirPin, int steps) {
  bool direction = (steps >= 0) ? HIGH : LOW;
  steps = abs(steps);
  digitalWrite(dirPin, direction);
  for (int i = 0; i < steps; i++) {
    digitalWrite(stepPin, HIGH);
    delayMicroseconds(1000);
    digitalWrite(stepPin, LOW);
    delayMicroseconds(1000);
  }
}

void checkCarInSpot() {
  // Send trigger pulse
  digitalWrite(triggerPin, LOW);
  delayMicroseconds(2);
  digitalWrite(triggerPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(triggerPin, LOW);

  // Measure echo pulse duration
  long duration = pulseIn(echoPin, HIGH);
  int distance = duration * 0.034 / 2;

  // Update carDetected state
  if (distance < sensorThreshold && !carDetected) {
    carDetected = true;
  } else if (distance >= sensorThreshold && carDetected) {
    carDetected = false;
  }
}

void parseCommand(String command) {
  command.trim();

  if (command.startsWith("MOVE_VERTICAL_UP ")) {
    int steps = command.substring(16).toInt();
    moveMotor(vertStepPin, vertDirPin, steps);
    Serial.println("DONE");
  }
  else if (command.startsWith("MOVE_VERTICAL_DOWN")) {
    // Check if specific steps are provided
    if (command.length() > 18) { // "MOVE_VERTICAL_DOWN " is 18 characters
      int steps = command.substring(18).toInt();
      moveMotor(vertStepPin, vertDirPin, -steps);
    } else {
      // Default to moving down to ground level
      moveMotor(vertStepPin, vertDirPin, -stepsPerLevel);
    }
    Serial.println("DONE");
  }
  else if (command.startsWith("MOVE_HORIZONTAL_LEFT ")) {
    int steps = command.substring(20).toInt();
    moveMotor(leftStepPin, leftDirPin, steps);
    Serial.println("DONE");
  }
  else if (command.startsWith("MOVE_HORIZONTAL_RIGHT ")) {
    int steps = command.substring(21).toInt();
    moveMotor(rightStepPin, rightDirPin, steps);
    Serial.println("DONE");
  }
  else if (command.startsWith("MOVE_HORIZONTAL_TO_ELEVATOR")) {
    moveMotor(leftStepPin, leftDirPin, horizontalStepsToElevator);
    Serial.println("DONE");
  }
  else if (command.startsWith("MOVE_HORIZONTAL_TO_SPOT")) {
    moveMotor(leftStepPin, leftDirPin, horizontalStepsToSpot);
    Serial.println("DONE");
  }
  else if (command == "CHECK_SPOT") {
    if (carDetected) {
      Serial.println("Spot Occupied");
    } else {
      Serial.println("Spot Free");
    }
    Serial.println("DONE");
  }
  else {
    Serial.println("UNKNOWN_COMMAND");
    Serial.println("DONE");
  }
}

void loop() {
  checkCarInSpot();

  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    parseCommand(command);
  }
}
