#include <ESP32Servo.h>

struct Motor {
  Servo servo;
  const char* name;
  const int pin;

  Motor(const Servo& servo, const char* name, const int pin):
    servo(servo),
    name(name),
    pin(pin) {

    }
};

Motor motors[] = {
  Motor(Servo(), "lfl",  4), // Lateral Front Left
  Motor(Servo(), "lfr", 32), // Lateral Front Right
  Motor(Servo(), "lbl", 23), // Lateral Back Left
  Motor(Servo(), "lbr", 26), // Lateral Back Right

  Motor(Servo(), "vfl", 18), // Vertical Front Left
  Motor(Servo(), "vfr", 33), // Vertical Front Right
  Motor(Servo(), "vbl", 19), // Vertical Back Left
  Motor(Servo(), "vbr", 25)  // Vertical Back Right
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
          if ( (target.equalsIgnoreCase(motors[i].name) && (motors[i].pin != -1) ) ) {
            motors[i].servo.writeMicroseconds(throttle);
            break;
          }
        }
      }
    }
  }
}
