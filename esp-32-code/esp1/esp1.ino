#include <ESP32Servo.h>
#include <cstdlib>
#include <ctime>

enum motorState {
  REVERSING,
  AT_ZERO,
  NORMAL
};

template<typename T>
T sign(T num) {
  if (num < 0) {
    return -1;
  } else if (num > 0) {
    return 1;
  } else {
    return 0;
  }
}

template<typename T>
T clamp(T val, T min, T max) {
  if (val < min) {
    return min;
  } else if (val > max) {
    return max;
  } else {
    return val;
  }
}

unsigned short max_allowed_vertical(unsigned short num_lateral) {
  int max_allowed_amps = 26;
  float used_amps = 5.5 * num_lateral;
  float vertical_allowed_amps = min( (max_allowed_amps - used_amps) / 4.0, 0.0 );
  return (unsigned short)( (vertical_allowed_amps / 5.5) * 500);
}

struct MotorController {
  Servo motor;
  const char* name;
  const int pin;
  int pwm;
  int written_pwm;
  int offset;
  const int motor_reversed;
  motorState state;
  unsigned long stateTimer = 0;

  static const int MAX_INCREMENT = 20;
  static const unsigned long ZERO_DURATION = 1000;

  MotorController(const Servo& motor, const char* name, const int pin, const int motor_reversed):
    motor(motor),
    name(name),
    pin(pin),
    motor_reversed(motor_reversed),
    pwm(1500),
    written_pwm(0),
    offset(0),
    state(NORMAL) {

    }

  MotorController(const Servo& motor, const char* name, const int pin, const int motor_reversed, int offset):
    motor(motor),
    name(name),
    pin(pin),
    motor_reversed(motor_reversed),
    pwm(1500),
    written_pwm(0),
    offset(offset),
    state(NORMAL) {

    }
};

MotorController controllers[] = {
  MotorController(Servo(), "lfl", 17,  1), // Lateral Front Left - 1
  MotorController(Servo(), "lfr", 18,  1), // Lateral Front Right - 2
  MotorController(Servo(), "vfl", 19,  1), // Vertical Front Left - 3
  MotorController(Servo(), "vfr", 16,  1), // Vertical Front Right - 4
  MotorController(Servo(), "vbl",  4,  1), // Vertical Back Left - 5
  MotorController(Servo(), "vbr", 13,  1),  // Vertical Back Right - 6
  MotorController(Servo(), "lbl", 14,  1), // Lateral Back Left - 7
  MotorController(Servo(), "lbr", 27,  1) // Lateral Back Right - 8

};

const int num_motors = 8;

String offsets[] = {
  "lfl_offset",
  "lfr_offset",
  "lbl_offset",
  "lbr_offset"
};

unsigned short num_active_lateral = 0;

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
    if (controllers[i].pin != -1) {
      controllers[i].motor.attach(controllers[i].pin);
      controllers[i].motor.writeMicroseconds(controllers[i].pwm); // Neutral position
      controllers[i].written_pwm = controllers[i].pwm;
    }
  }
  delay(750);
  for (int i = 0; i < num_motors; i++) {
    if (controllers[i].pin != -1) {
      controllers[i].motor.attach(controllers[i].pin);
      controllers[i].motor.writeMicroseconds(1100);
      controllers[i].written_pwm = 1100;
    }
  }
  delay(750);
  for (int i = 0; i < num_motors; i++) {
    if (controllers[i].pin != -1) {
      controllers[i].motor.attach(controllers[i].pin);
      controllers[i].motor.writeMicroseconds(controllers[i].pwm); // Neutral position
      controllers[i].written_pwm = controllers[i].pwm;
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
        controllers[i].offset = throttle;
        target_found = true;
        break;
      }
    }
    if (target_found) {
      continue;
    }

    if (throttle >= 1000 && throttle <= 2000) {
      for (int i = 0; i < num_motors; i++) {
        MotorController* motor = &controllers[i];
        if ( (target.equalsIgnoreCase(motor->name) && (motor->pin != -1) ) ) {
          int old_target = motor->pwm;
          motor->pwm = 1500 + ((throttle - 1500) * motor->motor_reversed);
          if (old_target != motor->pwm) {
            motor->state = NORMAL;
          }
          
          if (motor->name[0] == 'l') { // lateral motor (starts with l)
            if ((old_target == 1500) && (motor->written_pwm == 1500) && (motor->pwm != 1500)) {
              num_active_lateral++;
            }
          }
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
    MotorController* motor = &controllers[i];
    if (motor->pin != -1) {
      int target = motor->pwm + motor->offset - 1500;
      int current = motor->written_pwm - 1500;
      switch (motor->state) {
        case NORMAL:
          if ((sign<int>(target) * sign<int>(current)) == -1) {
            motor->state = REVERSING;
            target = 0;
          }
          break;
        case REVERSING:
          target = 0;
          if (current == 0) {
            motor->state = AT_ZERO;
            motor->stateTimer = millis();
          }
          break;
        case AT_ZERO:
          target = 0;
          if ((millis() - motor->stateTimer) >= MotorController::ZERO_DURATION) {
            motor->state = NORMAL;
          }
          break;
      }

      int current_speed = abs(current);
      int target_speed = abs(target);

      if ((motor->name[0]=='v') && (num_active_lateral > 0)) {
//         target_speed = clamp<unsigned short>(target_speed, 0, max_allowed_vertical(num_active_lateral));
      }
      if (target_speed < current_speed) {
        int command = sign<int>(current) * max(target_speed, current_speed - MotorController::MAX_INCREMENT);
        motor->motor.writeMicroseconds(command + 1500);
        motor->written_pwm = command + 1500;
      } else {
        motor->motor.writeMicroseconds(target + 1500);
        motor->written_pwm = target + 1500;
      }

      if (motor->name[0] == 'l') { // lateral motor (starts with l)
        if ((motor->pwm == 1500) && (motor->written_pwm == 1500) && (current != 0)) {
          num_active_lateral--;
        }
      }
    }
  }

  if ((millis() - current_time) >= 200) {
    // telemetry, for later
    // output = output.substring(0,output.length());
    // Serial.println(output);
//     Serial.println("Hello, World!");
    current_time = millis();
//     Serial.printf("pressure_sensor=%f,esp2_sensor=%d\n", num_active_lateral, controllers[5].written_pwm);
    Serial.print("pressure_sensor=");
//     Serial.println(num_active_lateral);
//     Serial.print("esp1_sensor=");
//     Serial.println(controllers[5].written_pwm);
    Serial.println(analogRead(pressure_sensor));
//     Serial.print(controllers[7].pwm);
//     Serial.print(" , ");
//     Serial.println(controllers[7].written_pwm);
  }
}
