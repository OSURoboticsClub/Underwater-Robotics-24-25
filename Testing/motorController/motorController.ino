#include <ESP32Servo.h>

Servo esc; // Create a Servo object for the ESC
const int escPin = 19; // ESC signal wire connected to pin 19

void setup() {
    Serial.begin(115200);  // Match with Jetson's ROS node
    esc.attach(escPin);
    esc.writeMicroseconds(1500); // Neutral position (for most ESCs)
}

void loop() {
    if (Serial.available()) {
        String input = Serial.readStringUntil('\n');
        input.trim();  // Remove any leading/trailing whitespace

        int throttle = 1500;  // Default to neutral
        if (input.length() > 0) {
            if (input.toInt() != 0) {
                // Just a number like 1600
                throttle = input.toInt();
            } else {
                // Full command like FWD 1600
                int spaceIndex = input.indexOf(' ');
                if (spaceIndex > 0) {
                    String command = input.substring(0, spaceIndex);
                    String valueStr = input.substring(spaceIndex + 1);
                    throttle = valueStr.toInt();
                    // You can check  if you want later
                }
            }

            // Bounds check
            if (throttle >= 1000 && throttle <= 2000) {
                esc.writeMicroseconds(throttle);
            } else {
                esc.writeMicroseconds(1500);  // Safety fallback
            }
        }
    }
}
