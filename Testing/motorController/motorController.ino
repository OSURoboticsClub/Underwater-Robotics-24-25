#include <ESP32Servo.h>

Servo esc; // Create a Servo object for the ESC
const int escPin = 19; // ESC signal wire connected to pin 19

void setup() {
    Serial.begin(9600);
    esc.attach(escPin);
    esc.writeMicroseconds(1500); // Neutral position (for most ESCs)
}

void loop() {
    if (Serial.available() > 0) {
        int throttle = Serial.parseInt();
        if (throttle >= 1450 && throttle <= 1550) {
          esc.writeMicroseconds(1500);
        } else if (throttle >= 1000 && throttle <= 2000) {
            esc.writeMicroseconds(throttle);
        }
    }
}
