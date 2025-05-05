#include <ESP32Servo.h>

struct Motor {
  Servo servo;
  const char* name;
  const int pin;
  const start_pos = 1500;

  Motor(const Servo& servo, const char* name, int pin):
    servo(servo),
    name(name),
    pin(pin) {}

  Motor(const Servo& servo, const char* name, int pin, int default_pos):
    servo(servo),
    name(name),
    pin(pin),
    start_pos(default_pos) {}
};

Motor motors[] = {
  Motor(Servo(), "main_manip", -1, 2500),
  Motor(Servo(), "left_manip", -1, 500),
  Motor(Servo(), "top_manip",  -1, 500),
  Motor(Servo(), "main_mover", -1),
  Motor(Servo(), "left_mover", -1),
};

const int num_motors = 5;

void setup() {
  Serial.begin(115200);  // Match with Jetson's ROS node

  for (int i = 0; i < num_motors; i++) {
    if (motors[i].pin != -1) {
      motors[i].servo.attach(motors[i].pin);
      motors[i].servo.writeMicroseconds(motors[i].start_pos); // Neutral position
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

      if (throttle >= 500 && throttle <= 2500) {
        for (int i = 0; i < num_motors; i++) {
          if ( (target.equalsIgnoreCase(motors[i].name) && (motors[i].pin != -1) ) ) {
            motors[i].servo.writeMicroseconds(throttle);
            break;
          }
        }
      }
    }
    //insert code  here theo
    //print to serial. py code to publish to serial output/sensor output
  } else if((millis() - current_time) >= 10) {
    Serial.println("Hello, World!");
    current_time = millis();
  }
}
