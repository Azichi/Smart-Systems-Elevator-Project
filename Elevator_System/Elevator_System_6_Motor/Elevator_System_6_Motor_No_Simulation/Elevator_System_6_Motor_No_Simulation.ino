// STEP and DIR pins for vertical motor
const int vertStepPin = 6;
const int vertDirPin = 7;

// STEP and DIR pins for horizontal motors
const int horizStepPins[6] = {8, 14, 16, 18, 20, 22};
const int horizDirPins[6] = {9, 15, 17, 19, 21, 23};

// Ultrasonic sensor pins
const int triggerPins[12] = {10, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44};
const int echoPins[12] = {11, 25, 27, 29, 31, 33, 35, 37, 39, 41, 43, 45};

// Constants
const int stepsPerLevel = 2000;
const int sensorThreshold = 15;
const int horizontalStepsToElevator = 1000;
const int horizontalStepsToSpot = 1000;
const int verticalStepsDown = 2000;
const int verticalStepsUp = 2000;

// Test mode
bool testMode = true;

void setup() {
    Serial.begin(9600);
    for (int i = 0; i < 12; i++) {
        pinMode(triggerPins[i], OUTPUT);
        pinMode(echoPins[i], INPUT);
    }
    pinMode(vertStepPin, OUTPUT);
    pinMode(vertDirPin, OUTPUT);
    for (int i = 0; i < 6; i++) {
        pinMode(horizStepPins[i], OUTPUT);
        pinMode(horizDirPins[i], OUTPUT);
    }
}

void moveMotor(int stepPin, int dirPin, int steps) {
    bool direction = (steps >= 0) ? HIGH : LOW;
    steps = abs(steps);
    digitalWrite(dirPin, direction);
    for (int i = 0; i < steps; i++) {
        digitalWrite(stepPin, HIGH);
        delayMicroseconds(500);
        digitalWrite(stepPin, LOW);
        delayMicroseconds(500);
    }
}

long measureDistance(int triggerPin, int echoPin) {
    long duration, distance;
    digitalWrite(triggerPin, LOW);
    delayMicroseconds(2);
    digitalWrite(triggerPin, HIGH);
    delayMicroseconds(10);
    digitalWrite(triggerPin, LOW);
    duration = pulseIn(echoPin, HIGH);
    distance = duration * 0.034 / 2;
    return distance;
}

void parseCommand(String command) {
    command.trim();
    if (command.startsWith("MOVE_VERTICAL_UP ")) {
        int steps = command.substring(16).toInt();
        moveMotor(vertStepPin, vertDirPin, steps);
        Serial.println("DONE");
    }
    else if (command.startsWith("MOVE_VERTICAL_DOWN")) {
        if (command.length() > 18) {
            int steps = command.substring(18).toInt();
            moveMotor(vertStepPin, vertDirPin, -steps);
        } else {
            moveMotor(vertStepPin, vertDirPin, -stepsPerLevel);
        }
        Serial.println("DONE");
    }
    else if (command.startsWith("MOVE_HORIZONTAL_LEFT ")) {
        int steps = command.substring(20).toInt();
        moveMotor(horizStepPins[0], horizDirPins[0], steps);
        Serial.println("DONE");
    }
    else if (command.startsWith("MOVE_HORIZONTAL_RIGHT ")) {
        int steps = command.substring(21).toInt();
        moveMotor(horizStepPins[0], horizDirPins[0], steps);
        Serial.println("DONE");
    }
    else if (command.startsWith("MOVE_HORIZONTAL_TO_ELEVATOR")) {
        moveMotor(horizStepPins[0], horizDirPins[0], horizontalStepsToElevator);
        Serial.println("DONE");
    }
    else if (command.startsWith("MOVE_HORIZONTAL_TO_SPOT")) {
        moveMotor(horizStepPins[0], horizDirPins[0], horizontalStepsToSpot);
        Serial.println("DONE");
    }
    else if (command.startsWith("MOVE HORIZONTAL")) {
        int level = command.substring(15, 16).toInt();
        int space = command.indexOf(' ', 17);
        String direction = command.substring(17, space);
        float distance = command.substring(space + 1).toFloat();
        if (!testMode || level <= 6) {
            moveMotor(horizStepPins[level - 1], horizDirPins[level - 1], distance * 10);
            Serial.println("DONE");
        } else {
            Serial.println("DONE");
        }
    }
    else if (command.startsWith("MOVE VERTICAL")) {
        int level = command.substring(12, 13).toInt();
        int space = command.indexOf(' ', 14);
        String direction = command.substring(14, space);
        float distance = command.substring(space + 1).toFloat();
        if (!testMode || level == 1) {
            moveMotor(vertStepPin, vertDirPin, (direction == "UP" ? 1 : -1) * distance * 10);
            Serial.println("DONE");
        } else {
            Serial.println("DONE");
        }
    }
    else if (command == "CHECK_SPOT") {
        long distance = measureDistance(triggerPins[0], echoPins[0]);
        if (distance < sensorThreshold) {
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
    if (Serial.available() > 0) {
        String command = Serial.readStringUntil('\n');
        parseCommand(command);
    }
}
