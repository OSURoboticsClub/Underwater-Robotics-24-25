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

#include "ESP32_NOW_Serial.h"
#include "MacAddress.h"
#include "WiFi.h"

#include "esp_wifi.h"

// 0: AP mode, 1: Station mode
#define ESPNOW_WIFI_MODE_STATION 1

// Channel to be used by the ESP-NOW protocol
#define ESPNOW_WIFI_CHANNEL 1

#if ESPNOW_WIFI_MODE_STATION          // ESP-NOW using WiFi Station mode
#define ESPNOW_WIFI_MODE WIFI_STA     // WiFi Mode
#define ESPNOW_WIFI_IF   WIFI_IF_STA  // WiFi Interface
#else                                 // ESP-NOW using WiFi AP mode
#define ESPNOW_WIFI_MODE WIFI_AP      // WiFi Mode
#define ESPNOW_WIFI_IF   WIFI_IF_AP   // WiFi Interface
#endif

// Set the MAC address of the device that will receive the data
// For example: F4:12:FA:40:64:4C
const MacAddress peer_mac({0x98, 0x3D, 0xAE, 0xA9, 0xEE, 0x44});
// 98:3D:AE:A9:EE:44

ESP_NOW_Serial_Class NowSerial(peer_mac, ESPNOW_WIFI_CHANNEL, ESPNOW_WIFI_IF);

#define BUFFER_SIZE 160
String input_string, target, output;
void setup() {
  input_string.reserve(BUFFER_SIZE);
  target.reserve(16);
  output.reserve(16);
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

enum floatState {
  INITIAL,
  SENSING,
  WAITING,
  SENDING
};

void process_command(String &input);

floatState state = INITIAL;
unsigned long timer = 0;

char rx_buffer[BUFFER_SIZE];
uint8_t rx_index = 0;
void loop() {
  while (NowSerial.available()) {
    char c = NowSerial.read();

    if (c != '\n') {
      if (c == '\t' || c == ' ') {
        continue;
      }

      if (rx_index < (BUFFER_SIZE-1)) {
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

  switch(state) {
    case INITIAL:
      if ((millis() - timer) >= 100) {
        output = "sensor data\n";
        timer = millis();
      }
      break;
    case SENSING:
      break;
    case WAITING:
      break;
    case SENDING:
      break;
  }

  while (output != "" && NowSerial.availableForWrite()) {
    char c = output[0];
    if (NowSerial.write(c) <= 0) {
      Serial.println("Failed to send data");
      continue;
    } else {
      output.remove(0,1);
    }
  }

  delay(1);
}

void process_command(String &input) {
  input.trim();
  switch(state) {
    case INITIAL:
      target = "dive";
      if (input.equals(target)) {
        state = SENSING;
      }
      break;
    case WAITING:
      target = "release";
      if (input.equals(target)) {
        state = SENDING;
      }
      break;
    default:
      target = "reset";
      if (input.equals(target)) {
        state = INITIAL;
      }
      break;
  }

  Serial.print("State: ");
  switch(state) {
    case INITIAL:
      Serial.println("initial");
      break;
    case SENSING:
      Serial.println("sensing");
      break;
    case WAITING:
      Serial.println("waiting");
      break;
    case SENDING:
      Serial.println("sending");
      break;
  }

  // Serial.println(input);
  // if (target != "") {
  //   Serial.println(target);
  // }

}