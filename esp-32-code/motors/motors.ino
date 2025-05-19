#include <ESP32Servo.h>
#include <cstdlib>
#include <ctime>

struct Motor {
  Servo servo;
  const char* name;
  const int pin;
  int pwm;
  int offset;

  Motor(const Servo& servo, const char* name, const int pin):
    servo(servo),
    name(name),
    pin(pin),
    pwm(1500),
    offset(0) {

    }

  Motor(const Servo& servo, const char* name, const int pin, int offset):
    servo(servo),
    name(name),
    pin(pin),
    pwm(1500),
    offset(offset) {

    }
};

Motor motors[] = {
  Motor(Servo(), "lfl",  4), // Lateral Front Left
  Motor(Servo(), "lfr", 32, -404), // Lateral Front Right
  Motor(Servo(), "lbl", 26, -394), // Lateral Back Left
  Motor(Servo(), "lbr", 23, -394), // Lateral Back Right

  Motor(Servo(), "vfl", 18), // Vertical Front Left
  Motor(Servo(), "vfr", 33), // Vertical Front Right
  Motor(Servo(), "vbl", 19), // Vertical Back Left
  Motor(Servo(), "vbr", 25)  // Vertical Back Right
};

const int num_motors = 8;

String offsets[] = {
  "lfl_offset",
  "lfr_offset",
  "lbl_offset",
  "lbr_offset"
};

void setup() {
  Serial.begin(115200);  // Match with Jetson's ROS node
  delay(2000);
  srand(time(nullptr));

  for (int i = 0; i < num_motors; i++) {
    if (motors[i].pin != -1) {
      motors[i].servo.attach(motors[i].pin);
      motors[i].servo.writeMicroseconds(motors[i].pwm); // Neutral position
    }
  }
  delay(750);
  for (int i = 0; i < num_motors; i++) {
    if (motors[i].pin != -1) {
      motors[i].servo.attach(motors[i].pin);
      motors[i].servo.writeMicroseconds(1100);
    }
  }
  delay(750);
  for (int i = 0; i < num_motors; i++) {
    if (motors[i].pin != -1) {
      motors[i].servo.attach(motors[i].pin);
      motors[i].servo.writeMicroseconds(motors[i].pwm); // Neutral position
    }
  }
}

long current_time = millis();
void loop() {
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    input.trim();  // Remove any leading/trailing whitespace

    int space_index = input.indexOf(' ');
    if (space_index > 0) {
      String target = input.substring(0, space_index);
      int throttle = input.substring(space_index + 1).toInt();

      for (int i = 0; i < 4; i++) {
        if (target.equalsIgnoreCase(offsets[i])) {
          motors[i].offset = throttle;
          motors[i].servo.writeMicroseconds(motors[i].pwm + motors[i].offset); // Neutral position
          
          if ((millis() - current_time) >= 100) {
            String output = "";
            output += motors[i].name;
            output += " ";
            output += (motors[i].pwm + motors[i].offset);
            Serial.println(output);
          }
          current_time = millis();
          return;
        }
      }
      if (throttle >= 1000 && throttle <= 2000) {
        for (int i = 0; i < num_motors; i++) {
          if ( (target.equalsIgnoreCase(motors[i].name) && (motors[i].pin != -1) ) ) {
            motors[i].pwm = throttle;
            motors[i].servo.writeMicroseconds(motors[i].pwm + motors[i].offset); // Neutral position
            
            if ((millis() - current_time) >= 100) {
              String output = "";
              output += motors[i].name;
              output += " ";
              output += (motors[i].pwm + motors[i].offset);
              Serial.println(output);
            }
            current_time = millis();
            return;
          }
        }
      }
    }
  }
}
