#include <ESP32Servo.h>
#include <cstdlib>
#include <ctime>

struct Motor {
  Servo servo;
  const char* name;
  const int pin;
  const int low = 1000;
  const int high = 2000;
  int current_max;
  int pwm;
  int written_pwm;

  Motor(const Servo& servo, const char* name, int pin):
    servo(servo),
    name(name),
    pin(pin),
    pwm(1500) {
      this->current_max = this->high;
      this->written_pwm = 0;
    }

  Motor(const Servo& servo, const char* name, int pin, int default_pos):
    servo(servo),
    name(name),
    pin(pin),
    pwm(default_pos) {
      this->current_max = this->high;
      this->written_pwm = 0;
    }

  Motor(const Servo& servo, const char* name, int pin, int default_pos, int low, int high):
    servo(servo),
    name(name),
    pin(pin),
    pwm(default_pos),
    low(low),
    high(high) {
      this->current_max = this->high;
      this->written_pwm = 0;
    }
};

Motor motors[] = {
  Motor(Servo(), "manip_rotate",  25), // rotates the claw
  // Motor(Servo(), "ext_lights", 26, 1000, 1000, 1900), // change defaults
  Motor(Servo(), "camera_x",  4, 1500, 1200, 1800), // change default
  Motor(Servo(), "camera_y", 16, 1500, 1100, 1900) // change defaults
//   Motor(Servo(), "main_mover", 25), // rotates the claw
//   Motor(Servo(), "left_mover", -1), // moves the syringe thingy
};
const int num_motors = 3;

const int manip = 13;
const int dome_lights = -1;
const int ext_lights = 26;

/*
   Possible input keys:
   camera_x - 7 digits
   camera_y - 7 digits
   dome_lights_max - 3 digits
   ext_lights_max - 3 digits
   manip - 3 digits
   manip_rotate - 4 digits
   dome_lights - 3 digits
   ext_lights - 3 digits
 */

#define BUFFER_SIZE 160
String input_string, cmd, target, value;
void setup() {
  cmd.reserve(24);
  target.reserve(16);
  value.reserve(8);
  Serial.begin(115200);  // Match with Jetson's ROS node

  for (int i = 0; i < num_motors; i++) {
    if (motors[i].pin != -1) {
      motors[i].servo.attach(motors[i].pin);
      motors[i].servo.writeMicroseconds(motors[i].pwm); // Neutral position
      motors[i].written_pwm = motors[i].pwm;
    }
  }

  pinMode(manip, OUTPUT);
  pinMode(dome_lights, OUTPUT);
  pinMode(ext_lights, OUTPUT);
  pinMode(18, OUTPUT);
  pinMode(19, OUTPUT);

  digitalWrite(manip, LOW);
  digitalWrite(dome_lights, LOW);
  digitalWrite(ext_lights, LOW);
  digitalWrite(18, HIGH);
  digitalWrite(19, HIGH);


}

void process_commands(String &input) {  
  int start=0;
  int end=0;
  while (start < input.length()) {
    end = input.indexOf(',', start);
    if (end == -1) {
      end = input.length();
    }

    cmd = input.substring(start, end);
    start = end + 1;

    int eq_index = cmd.indexOf('=');
    if (eq_index == -1) {
      continue;
    }

    bool target_found = false;
    target = cmd.substring(0, eq_index);
    value = cmd.substring(eq_index + 1);

    if (target == "camera_x") {
      int i = 1;
      int throttle = value.toInt();
      if (throttle >= motors[i].low && throttle <= motors[i].current_max) {
        motors[i].pwm = throttle;
      }
    } else if (target == "camera_y") {
      int i = 2;
      int throttle = value.toInt();
      if (throttle >= motors[i].low && throttle <= motors[i].current_max) {
        motors[i].pwm = throttle;
      }
    } else if (target == "dome_lights_max") {
      // later will be used
    } else if (target == "ext_lights_max") {
      /*
      int i = 1;
      double scale = value.toDouble();
      int range = motors[i].high - motors[i].low;
      motors[i].current_max = motors[i].low + int(scale * range);
      motors[i].pwm = min(motors[i].current_max, motors[i].pwm);
      */
    } else if (target == "manip") {
      int throttle = value.toInt();
      if (throttle == 0) {
        digitalWrite(manip, LOW);
        Serial.println("Closing manip");
      } else {
        digitalWrite(manip, HIGH);
        Serial.println("Opening manip");
      }
    } else if (target == "manip_rotate") {
      int i = 0;
      int throttle = value.toInt();
      if (throttle >= motors[i].low && throttle <= motors[i].current_max) {
        Serial.println("Setting manipulator to new value");
        motors[i].pwm = throttle;
      }
    } else if (target == "dome_lights") {
      int throttle = value.toInt();
      if (throttle == 0) {
        digitalWrite(dome_lights, LOW);
      } else {
        digitalWrite(dome_lights, HIGH);
      }
    } else if (target == "ext_lights") {
      int throttle = value.toInt();
      if (throttle == 0) {
        digitalWrite(ext_lights, LOW);
        Serial.println("Turning lights off");
      } else {
        digitalWrite(ext_lights, HIGH);
        Serial.println("Turning lights on");
      }

      /*
         int i = 1;
         int throttle = value.toInt();
         if (throttle == 0) {
         motors[i].pwm = motors[i].low;
         } else if (throttle == 1) {
         motors[i].pwm = motors[i].current_max;
         }
         */
    }
  }
}

char rx_buffer[BUFFER_SIZE];
uint8_t rx_index = 0;
long current_time = millis();
void loop() {
  while (Serial.available()) {
    char c = Serial.read();

    if (c != '\n') {
      if (c == '\t' || c == ' ') {
        continue;
      }

      if (rx_index < (BUFFER_SIZE - 1)) {
        rx_buffer[rx_index++] = c;
      } else {
        rx_index = 0;
      }
    } else {
      rx_buffer[rx_index] = '\0';
      input_string = rx_buffer;
      process_commands(input_string);
      rx_index = 0;
      break;
    }
  }

  for (int i = 0; i < num_motors; i++) {
    if ((motors[i].pin != -1) && (motors[i].written_pwm != motors[i].pwm)) {
      motors[i].servo.writeMicroseconds(motors[i].pwm);
      motors[i].written_pwm = motors[i].pwm;
    }
  }

  if ((millis() - current_time) >= 100) {
    // telemetry, for later
    // output = output.substring(0,output.length());
    // Serial.println(output);
    // Serial.println("Hello, World!");
    // current_time = millis();
    // Serial.println(motors[3].written_pwm);
  }

  //   if (Serial.available()) {
  //     String input = Serial.readStringUntil('\n');
  //     input.trim();  // Remove any leading/trailing whitespace
  // 
  //     int space_index = input.indexOf(' ');
  //     if (space_index > 0) {
  //       String target = input.substring(0, space_index);
  // 
  //       int target_pin = 0;
  //       if (target.equalsIgnoreCase("main_manip")) {
  //         target_pin = main_manip;
  //       } else if (target.equalsIgnoreCase("left_manip")) {
  //         target_pin = left_manip;
  //       } else if (target.equalsIgnoreCase("lights")) {
  //         target_pin = lights;
  //       }
  // 
  //       int throttle = input.substring(space_index + 1).toInt();
  // 
  //       if (target_pin != 0) {
  //         if (throttle == 0.0) {
  //           digitalWrite(target_pin, LOW);
  //         } else {
  //           digitalWrite(target_pin, HIGH);
  //         }
  //       } else if (throttle >= 500 && throttle <= 2500) {
  //         for (int i = 0; i < num_motors; i++) {
  //           if ( (target.equalsIgnoreCase(motors[i].name) && (motors[i].pin != -1) ) ) {
  //             motors[i].servo.writeMicroseconds(throttle);
  //             break;
  //           }
  //         }
  //       }
  //     }
  //   } 
}
