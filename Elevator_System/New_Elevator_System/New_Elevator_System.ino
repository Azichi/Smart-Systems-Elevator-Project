// STEP and DIR pins for each motor
const int vertStepPin = 6;
const int vertDirPin = 7;
const int leftStepPin = 8;
const int leftDirPin = 9;
const int rightStepPin = 12;
const int rightDirPin = 13;

// Ultrasonic sensor pins
const int triggerPin = 10;
const int echoPin = 11;

// Threshold distance (in cm) to detect if the car is in the parking spot
const int occupiedThreshold = 15;

bool carDetected = false;

void setup() {
  Serial.begin(9600);
  pinMode(vertStepPin, OUTPUT);
  pinMode(vertDirPin, OUTPUT);
  pinMode(leftStepPin, OUTPUT);
  pinMode(leftDirPin, OUTPUT);
  pinMode(rightStepPin, OUTPUT);
  pinMode(rightDirPin, OUTPUT);
  pinMode(triggerPin, OUTPUT);
  pinMode(echoPin, INPUT);
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
  digitalWrite(triggerPin, LOW);
  delayMicroseconds(2);
  digitalWrite(triggerPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(triggerPin, LOW);

  long duration = pulseIn(echoPin, HIGH);
  int distance = duration * 0.034 / 2;

  if (distance < occupiedThreshold && !carDetected) {
    Serial.println("Car in Spot");
    carDetected = true;
  } else if (distance >= occupiedThreshold && carDetected) {
    carDetected = false;
  }
}

void loop() {
  checkCarInSpot();

  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    if (command == "CHECK_SPOT") {
      if (carDetected) {
        Serial.println("Spot Occupied");
      } else {
        Serial.println("Spot Free");
      }
      Serial.println("DONE");
    } else if (command == "LOAD_CAR") {
      Serial.println("Car Loaded");
      Serial.println("DONE");
    } else if (command.startsWith("MOVE_VERTICAL_UP ")) {
      int steps = command.substring(16).toInt();
      moveMotor(vertStepPin, vertDirPin, steps);
      Serial.print("Elevator moved up by ");
      Serial.print(steps);
      Serial.println(" steps");
      Serial.println("DONE");
    } else if (command.startsWith("MOVE_VERTICAL_DOWN ")) {
      int steps = command.substring(18).toInt();
      moveMotor(vertStepPin, vertDirPin, -steps);
      Serial.print("Elevator moved down by ");
      Serial.print(steps);
      Serial.println(" steps");
      Serial.println("DONE");
    } else if (command.startsWith("MOVE_HORIZONTAL_LEFT ")) {
      int steps = command.substring(20).toInt();
      moveMotor(leftStepPin, leftDirPin, steps);
      Serial.print("Left horizontal motor moved left by ");
      Serial.print(steps);
      Serial.println(" steps");
      Serial.println("DONE");
    } else if (command.startsWith("MOVE_HORIZONTAL_RIGHT ")) {
      int steps = command.substring(21).toInt();
      moveMotor(rightStepPin, rightDirPin, steps);
      Serial.print("Right horizontal motor moved right by ");
      Serial.print(steps);
      Serial.println(" steps");
      Serial.println("DONE");
    } else {
      Serial.println("Unknown command");
      Serial.println("DONE");
    }
  }
}
