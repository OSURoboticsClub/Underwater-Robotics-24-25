#include <ESP32Servo.h>

struct Motor {
    Servo servo;
    const char* name;
    const int pin;
};

Motor motors[] = {
    {Servo, "lfl", 19}, // Lateral Front Left
    {Servo, "lfr", -1}, // Lateral Front Right
    {Servo, "lbl", -1}, // Lateral Back Left
    {Servo, "lbr", -1}, // Lateral Back Right

    {Servo, "vfl", -1}, // Vertical Front Left
    {Servo, "vfr", -1}, // Vertical Front Right
    {Servo, "vbl", -1}, // Vertical Back Left
    {Servo, "vbr", -1}  // Vertical Back Right
};

const int num_motors = 8;

void setup() {
    Serial.begin(115200);  // Match with Jetson's ROS node

    for (int i = 0; i < num_motors; i++) {
        if (motors[i].pin != -1) {
            motors[i].servo.attach(motors[i].pin);
            motors[i].servo.writeMicroseconds(1500); // Neutral position
        }
    }
}

void loop() {
    if (Serial.available()) {
        String input = Serial.readStringUntil('\n');
        input.trim();  // Remove any leading/trailing whitespace

        int space_index = input.indexOf(' ');
        if (space_index > 0) {
            String target = input.substring(0, space_index);
            int throttle = input.substring(space_index + 1).toInt();

            if (throttle >= 1000 && throttle <= 2000) {
                for (int i = 0; i < num_motors; i++) {
                    if ( target.equalsIgnoreCase(motors[i].name) ) {
                        motors[i].servo.writeMicroseconds(throttle);
                        break;
                    }
                }
            }
        }
    }
}
