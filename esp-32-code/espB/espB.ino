/*
    ESP-NOW Serial Example - Unicast transmission
    Lucas Saavedra Vaz - 2024
    Send data between two ESP32s using the ESP-NOW protocol in one-to-one (unicast) configuration.
    Note that different MAC addresses are used for different interfaces.
    The devices can be in different modes (AP or Station) and still communicate using ESP-NOW.
    The only requirement is that the devices are on the same Wi-Fi channel.
    Set the peer MAC address according to the device that will receive the data.

    Example setup:
    - Device 1: AP mode with MAC address F6:12:FA:42:B6:E8
                Peer MAC address set to the Station MAC address of Device 2 (F4:12:FA:40:64:4C)
    - Device 2: Station mode with MAC address F4:12:FA:40:64:4C
                Peer MAC address set to the AP MAC address of Device 1 (F6:12:FA:42:B6:E8)

    The device running this sketch will also receive and print data from any device that has its MAC address set as the peer MAC address.
    To properly visualize the data being sent, set the line ending in the Serial Monitor to "Both NL & CR".
*/

#include "AccelStepper.h"

#include "ESP32_NOW_Serial.h"
#include "MacAddress.h"
#include "WiFi.h"

#include "esp_wifi.h"

// 0: AP mode, 1: Station mode
#define ESPNOW_WIFI_MODE_STATION 1

// Channel to be used by the ESP-NOW protocol
#define ESPNOW_WIFI_CHANNEL 1

#if ESPNOW_WIFI_MODE_STATION        // ESP-NOW using WiFi Station mode
#define ESPNOW_WIFI_MODE WIFI_STA   // WiFi Mode
#define ESPNOW_WIFI_IF WIFI_IF_STA  // WiFi Interface
#else                               // ESP-NOW using WiFi AP mode
#define ESPNOW_WIFI_MODE WIFI_AP    // WiFi Mode
#define ESPNOW_WIFI_IF WIFI_IF_AP   // WiFi Interface
#endif

// Set the MAC address of the device that will receive the data
// For example: F4:12:FA:40:64:4C
const MacAddress peer_mac({ 0x98, 0x3D, 0xAE, 0xA9, 0xEE, 0x44 });
// 98:3D:AE:A9:EE:44

ESP_NOW_Serial_Class NowSerial(peer_mac, ESPNOW_WIFI_CHANNEL, ESPNOW_WIFI_IF);

/* Create an enum to represent the float states */
enum floatState {
  INITIAL,
  SENSING,
  WAITING,
  SENDING
};

/* Define a data packet */
#define PACKET_LENGTH 32
struct packet {
  static inline const char companyName[5] = "EX31";
  unsigned long time;
  unsigned short pressure;

  char* print(char print_str[PACKET_LENGTH]) {
    unsigned long pascals = ((unsigned long long)(this->pressure) * 1200000) / 4095;
    double meters = ((double)(this->pressure) * 1200000) / (9.8 * 1000 * 4095);
    snprintf(print_str, PACKET_LENGTH, "%.7s,%lu,%lu,%.2f\n", 
      this->companyName, this->time, pascals % 10000000, meters);
    return print_str;
  }
};

/* Set pin values */
const int stepPin = 10;
const int dirPin = 9;
const int buttonPin = 3;
const int sensorPin = 2;

/* Initialize stepper motor object */
const int MAX_STEPPER_VAL = 1800;
AccelStepper stepper(
  AccelStepper::DRIVER,
  stepPin,
  dirPin);

packet data[1000];
#define BUFFER_SIZE 160
String input_string, target, output;
void setup() {
  /* Preemptively allocate arrays for the expected string size. */
  input_string.reserve(BUFFER_SIZE);
  target.reserve(16);
  output.reserve(BUFFER_SIZE);

  /* Setup hardware */
  stepper.setMaxSpeed(1000);
  stepper.setAcceleration(500);
  pinMode(buttonPin, INPUT_PULLUP);

  /* Initialize the data array */
  for (int i = 0; i < 1000; i++) {
    data[i] = packet();
  }


  /* Setup wireless connection */
  Serial.begin(115200);

  Serial.print("WiFi Mode: ");
  Serial.println(ESPNOW_WIFI_MODE == WIFI_AP ? "AP" : "Station");
  WiFi.mode(ESPNOW_WIFI_MODE);

  Serial.print("Channel: ");
  Serial.println(ESPNOW_WIFI_CHANNEL);
  WiFi.setChannel(ESPNOW_WIFI_CHANNEL, WIFI_SECOND_CHAN_NONE);

  while (!(WiFi.STA.started() || WiFi.AP.started())) {
    delay(100);
  }

  Serial.print("MAC Address: ");
  Serial.println(ESPNOW_WIFI_MODE == WIFI_AP ? WiFi.softAPmacAddress() : WiFi.macAddress());

  // Start the ESP-NOW communication
  Serial.println("ESP-NOW communication starting...");
  NowSerial.begin(115200);
  Serial.printf("ESP-NOW version: %d, max data length: %d\n", ESP_NOW.getVersion(), ESP_NOW.getMaxDataLen());
  Serial.println("You can now send data to the peer device using the Serial Monitor.\n");
}

/* Forward declaration of input processing command */
void process_command(String& input);

/* Setup global variables to track data between loop cycles */
floatState state = INITIAL;
unsigned long timer = 0;
unsigned short data_idx = 0;
unsigned short data_length = 0;

// offsets: 13.0cm from top, 47.5 from bottom
const short lower_points[4] = {57, 7, 57, 7};
const short set_points[4] = {68, 18, 68, 18};
const short upper_points[4] = {79, 29, 79, 29};
int set_point_num = 0;
int data_point_num = 0;

char rx_buffer[BUFFER_SIZE];
uint8_t rx_index = 0;
void loop() {
  /* 
  Read from the wireless serial until a newline character is received
  Once one is received, take that whole line and pass it to the process_command function
  */
  while (NowSerial.available()) {
    char c = NowSerial.read();

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
      process_command(input_string);
      rx_index = 0;
      break;
    }
  }

  /* If the button is pressed, reset the stepper motor to consider this position to be 0 */
  bool button_pressed = !(digitalRead(buttonPin));

  /* Control the float based on its state */
  switch (state) {
    case INITIAL:  // Float is waiting for dive command and constantly sending packets
      /* If it has been at least 1 second since we sent a packet, send another one */
      if ((millis() - timer) >= 1000) {
        // Make a packet
        packet tmp = packet();

        // Set the values for the packet
        tmp.time = millis();
        tmp.pressure = analogRead(sensorPin);
//         tmp.pressure = 4095;

        // Print the packet
        char buf[PACKET_LENGTH];
        output += tmp.print(buf);

        // Start the timer
        Serial.println("Sending initial packet");
        timer = millis();
      }
        stepper.setSpeed(-300.0);
        if (button_pressed) {
          stepper.setCurrentPosition(0);
        }
        stepper.run();
      break;
    case SENSING:  // Float is profiling/sensing
//       if (data_length >= 50) {
//         state = WAITING;
//         Serial.println("State: waiting");
//       } else if ((millis() - timer) >= 100) {
//         if (data_length >= 1000) {
//           data_length = 0;
//           data_idx = 0;
//         }
// 
//         data_length++;
//         data[data_idx].time = millis();
//         // data[data_idx].pressure = data_idx;
//         data[data_idx].pressure = rand() % 4096;
//         data_idx++;
//         timer = millis();
//         Serial.printf("Saving datapoint #%i\n", data_idx);
//       }
      if (button_pressed) {
        stepper.setCurrentPosition(0);
      }

      if (set_point_num < 4) {
        if (data_point_num < 7) {
          short lower = lower_points[set_point_num];
          short set_point = set_points[set_point_num];
          short upper = upper_points[set_point_num];
          short sensor_data = analogRead(sensorPin);
          stepper.setSpeed(controller(sensor_data, set_point));
//           output = output + "Sensor: " + sensor_data + ", Speed: " + stepper.speed() + '\n';
          if ( (millis() - timer) >= 5000) {
            if (data_length >= 1000) {
              data_length = 0;
              data_idx = 0;
            }

            data_length++;
            data[data_idx].time = millis();
            data[data_idx].pressure = sensor_data;
            data_idx++;
            Serial.printf("Saving datapoint #%i\n", data_idx);

            if ( (lower <= sensor_data) && (sensor_data <= upper) ) {
              data_point_num++;
            } else {
              data_point_num = 0;
            }

            timer = millis();
          }
        } else {
          set_point_num++;
          data_point_num = 0;
        }
      } else {
        state = WAITING;
        Serial.println("State: waiting");
      }

//       output = output+"Current: "+stepper.currentPosition()+", Target: "+stepper.targetPosition()+'\n';
      if (
        !((stepper.speed() < 0) && (stepper.currentPosition() <= 0)) && 
        !((stepper.speed() > 0) && (stepper.currentPosition() >= MAX_STEPPER_VAL))
      ) {
        stepper.run();
      }
      break;
    case WAITING:
      break;
    case SENDING:
      if (data_idx > data_length - 1) {
        state = WAITING;
        Serial.println("State: waiting");
      } else if (output == "") {
        char buf[PACKET_LENGTH];
        output += data[data_idx].print(buf);
        data_idx++;
      }
      break;
  }


  while (output != "" && NowSerial.availableForWrite()) {
    char c = output[0];
    if (NowSerial.write(c) <= 0) {
      Serial.println("Failed to send data");
      continue;
    } else {
      output.remove(0, 1);
    }
  }

  delay(1);
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

double k_p = 15.0;  // TODO: tune this
float offset = 0.0;
float controller(short pressure, short set_point) {
  short err = set_point - pressure;
  return clamp<float>(-1 * err * k_p + offset, -300.0, 300.0);
}

void process_command(String& input) {
  input.trim();
  switch (state) {
    case INITIAL:
      target = "dive";
      if (input.equals(target)) {
        data_idx = 0;
        state = SENSING;
      }
      break;
    case WAITING:
      target = "release";
      if (input.equals(target)) {
        data_idx = 0;
        state = SENDING;
      }
      break;
  }

  target = "reset";
  if (input.equals(target)) {
    state = INITIAL;
    data_length = 0;
    data_idx = 0;
  }

  target = "proceed";
  if (input.equals(target)) {
    switch (state) {
      case INITIAL:
        state = SENSING;
        break;
      case SENSING:
        state = WAITING;
        break;
      case WAITING:
        state = SENDING;
        break;
      case SENDING:
        state = INITIAL;
        break;
    }
    data_idx = 0;
  }


  char* str;
  switch (state) {
    case INITIAL:
      str = "initial";
      break;
    case SENSING:
      str = "sensing";
      break;
    case WAITING:
      str = "waiting";
      break;
    case SENDING:
      str = "sending";
      break;
  }
  Serial.printf("State: %s\n", str);
}
