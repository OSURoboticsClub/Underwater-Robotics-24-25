#include <ESP32Servo.h>
#include <cstdlib>
#include <ctime>

struct Motor {
  Servo servo;
  const char* name;
  const int pin;
  int pwm;
  int written_pwm;
  int offset;

  Motor(const Servo& servo, const char* name, const int pin):
    servo(servo),
    name(name),
    pin(pin),
    pwm(1500),
    written_pwm(0),
    offset(0) {

    }

  Motor(const Servo& servo, const char* name, const int pin, int offset):
    servo(servo),
    name(name),
    pin(pin),
    pwm(1500),
    written_pwm(0),
    offset(offset) {

    }
};

Motor motors[] = {
  Motor(Servo(), "lfl",  4), // Lateral Front Left - 1
  Motor(Servo(), "lfr", 32, -404), // Lateral Front Right - 2
  Motor(Servo(), "lbl", 26, -394), // Lateral Back Left - 7
  Motor(Servo(), "lbr", 23, -394), // Lateral Back Right - 8

  Motor(Servo(), "vfl", 18), // Vertical Front Left - 3
  Motor(Servo(), "vfr", 33), // Vertical Front Right - 4
  Motor(Servo(), "vbl", 19), // Vertical Back Left - 5
  Motor(Servo(), "vbr", 25)  // Vertical Back Right - 6
};

const int num_motors = 8;

String offsets[] = {
  "lfl_offset",
  "lfr_offset",
  "lbl_offset",
  "lbr_offset"
};

#define BUFFER_SIZE 160
String input_string, cmd, target, value;
void setup() {
  cmd.reserve(24);
  target.reserve(16);
  value.reserve(8);
  input_string.reserve(BUFFER_SIZE);
  Serial.begin(115200);  // Match with Jetson's ROS node
  delay(2000);
  srand(time(nullptr));

  for (int i = 0; i < num_motors; i++) {
    if (motors[i].pin != -1) {
      motors[i].servo.attach(motors[i].pin);
      motors[i].servo.writeMicroseconds(motors[i].pwm); // Neutral position
      motors[i].written_pwm = motors[i].pwm;
    }
  }
  delay(750);
  for (int i = 0; i < num_motors; i++) {
    if (motors[i].pin != -1) {
      motors[i].servo.attach(motors[i].pin);
      motors[i].servo.writeMicroseconds(1100);
      motors[i].written_pwm = 1200;
    }
  }
  delay(750);
  for (int i = 0; i < num_motors; i++) {
    if (motors[i].pin != -1) {
      motors[i].servo.attach(motors[i].pin);
      motors[i].servo.writeMicroseconds(motors[i].pwm); // Neutral position
      motors[i].written_pwm = motors[i].pwm;
    }
  }
  delay(750);
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
    int throttle = value.toInt();

    for (int i = 0; i < 4; i++) {
      if (target.equalsIgnoreCase(offsets[i])) {
        motors[i].offset = throttle;
        target_found = true;
        break;
      }
    }
    if (target_found) {
      continue;
    }

    if (throttle >= 1000 && throttle <= 2000) {
      for (int i = 0; i < num_motors; i++) {
        if ( (target.equalsIgnoreCase(motors[i].name) && (motors[i].pin != -1) ) ) {
          motors[i].pwm = throttle;
          break;
        }
      }
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
    if ((motors[i].pin != -1) && (motors[i].written_pwm != (motors[i].pwm + motors[i].offset))) {
      motors[i].servo.writeMicroseconds(motors[i].pwm + motors[i].offset);
      motors[i].written_pwm = motors[i].pwm + motors[i].offset;
    }
  }

  if ((millis() - current_time) >= 100) {
    // telemetry, for later
    // output = output.substring(0,output.length());
    // Serial.println(output);
    // Serial.println("Hello, World!");
    current_time = millis();
    Serial.println(motors[0].written_pwm);
  }
}
