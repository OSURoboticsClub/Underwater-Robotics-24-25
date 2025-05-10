#include <ESP32Servo.h>

struct Motor {
  Servo servo;
  const char* name;
  const int pin;
  const int start_pos = 1500;

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
  Motor(Servo(), "top_manip",  13, 500),
  Motor(Servo(), "main_mover", 25),
  Motor(Servo(), "left_mover", 27),
  Motor(Servo(), "camera_x", 27),
  Motor(Servo(), "camera_y, 14")
};

const int main_manip = 26;
const int left_manip = 14;
const int lights = 2;

const int num_motors = 5;

void setup() {
  Serial.begin(115200);  // Match with Jetson's ROS node

  for (int i = 0; i < num_motors; i++) {
    if (motors[i].pin != -1) {
      motors[i].servo.attach(motors[i].pin);
      motors[i].servo.writeMicroseconds(motors[i].start_pos); // Neutral position
    }
  }

  pinMode(main_manip, OUTPUT);
  pinMode(left_manip, OUTPUT);
  pinMode(lights, OUTPUT);

  digitalWrite(main_manip, HIGH);
  digitalWrite(left_manip, LOW);
  digitalWrite(lights, LOW);
}

long current_time = millis();
void loop() {
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    input.trim();  // Remove any leading/trailing whitespace

    int space_index = input.indexOf(' ');
    if (space_index > 0) {
      String target = input.substring(0, space_index);

      int target_pin = 0;
      if (target.equalsIgnoreCase("main_manip")) {
        target_pin = main_manip;
      } else if (target.equalsIgnoreCase("left_manip")) {
        target_pin = left_manip;
      } else if (target.equalsIgnoreCase("lights")) {
        target_pin = lights;
      }

      int throttle = input.substring(space_index + 1).toInt();

      if (target_pin != 0) {
        if (throttle == 0.0) {
          digitalWrite(main_manip, LOW);
        } else {
          digitalWrite(main_manip, HIGH);
        }
      } else if (throttle >= 500 && throttle <= 2500) {
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
