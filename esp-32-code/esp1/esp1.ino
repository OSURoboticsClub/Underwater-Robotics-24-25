#include <ESP32Servo.h>
#include <cstdlib>
#include <ctime>

enum motorState {
  REVERSING,
  AT_ZERO,
  NORMAL
};

int sign(int num) {
  if (num < 0) {
    return -1;
  } else if (num > 0) {
    return 1;
  } else {
    return 0;
  }
}

struct Motor {
  Servo servo;
  const char* name;
  const int pin;
  int pwm;
  int written_pwm;
  int offset;
  const int reverse;
  motorState state;

  Motor(const Servo& servo, const char* name, const int pin, const int reverse):
    servo(servo),
    name(name),
    pin(pin),
    reverse(reverse),
    pwm(1500),
    written_pwm(0),
    offset(0),
    state(NORMAL) {

    }

  Motor(const Servo& servo, const char* name, const int pin, const int reverse, int offset):
    servo(servo),
    name(name),
    pin(pin),
    reverse(reverse),
    pwm(1500),
    written_pwm(0),
    offset(offset),
    state(NORMAL) {

    }
};

Motor motors[] = {
  Motor(Servo(), "lfl", 19,  1), // Lateral Front Left - 1
  Motor(Servo(), "lfr", 18,  1), // Lateral Front Right - 2
  Motor(Servo(), "vfl", 17,  1), // Vertical Front Left - 3
  Motor(Servo(), "vfr", 16,  1), // Vertical Front Right - 4
  Motor(Servo(), "vbl",  4,  1), // Vertical Back Left - 5
  Motor(Servo(), "vbr", 13,  1),  // Vertical Back Right - 6
  Motor(Servo(), "lbl", 14,  1), // Lateral Back Left - 7
  Motor(Servo(), "lbr", 27,  1) // Lateral Back Right - 8

};

const int num_motors = 8;

String offsets[] = {
  "lfl_offset",
  "lfr_offset",
  "lbl_offset",
  "lbr_offset"
};

const int pressure_sensor = 34;

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
      motors[i].written_pwm = 1100;
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

  pinMode(pressure_sensor, INPUT);
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
          int old_target = motors[i].pwm;
          motors[i].pwm = 1500 + ((throttle - 1500) * motors[i].reverse);
          if (old_target != motors[i].pwm) {
            motors[i].state = NORMAL;
          }
          break;
        }
      }
    }
  }
}

const int MAX_INCREMENT = 10;

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
    if (motors[i].pin != -1) {
      int target = motors[i].pwm + motors[i].offset - 1500;
      int current = motors[i].written_pwm - 1500;
      switch (motors[i].state) {
        case NORMAL:
          if ((sign(target) * sign(current)) == -1) {
            motors[i].state = REVERSING;
            target = 0;
          }
          break;
        case REVERSING:
          target = 0;
          if (current == 0) {
            motors[i].state = AT_ZERO;
          }
          break;
        case AT_ZERO:
          motors[i].state = NORMAL;
          target = 0;
          break;
      }

      int current_speed = abs(current);
      int target_speed = abs(target);
      if (target_speed < current_speed) {
        int command = sign(current) * max(target_speed, current_speed - MAX_INCREMENT);
        motors[i].servo.writeMicroseconds(command + 1500);
        motors[i].written_pwm = command + 1500;
      } else {
        motors[i].servo.writeMicroseconds(target + 1500);
        motors[i].written_pwm = target + 1500;
      }
    }
  }

  if ((millis() - current_time) >= 200) {
    // telemetry, for later
    // output = output.substring(0,output.length());
    // Serial.println(output);
//     Serial.println("Hello, World!");
    current_time = millis();
    Serial.println(analogRead(pressure_sensor));
//     Serial.print(motors[7].pwm);
//     Serial.print(" , ");
//     Serial.println(motors[7].written_pwm);
  }
}
