#include <WiFi.h>
#include <esp_wifi.h>
#include <Arduino.h>

#define SCANNER_SSID     "W1 Scanner"
#define SCAN_INTERVAL_MS 3000
#define CHANNEL_HOP_MS   2000
#define MAX_NETWORKS     30
#define SERIAL_BAUD      115200

static int currentChannel = 1;
static unsigned long lastScanTime = 0;
static unsigned long lastHopTime = 0;
static int scanCount = 0;

struct NetworkEntry {
  char ssid[33];
  uint8_t bssid[6];
  int32_t rssi;
  uint8_t channel;
  wifi_auth_mode_t encType;
};

static NetworkEntry networks[MAX_NETWORKS];
static int networkCount = 0;

void printRssiBar(int32_t rssi) {
  int bars = map(rssi, -100, -30, 0, 5);
  if (bars < 0) bars = 0;
  if (bars > 5) bars = 5;
  Serial.print("[");
  for (int i = 0; i < 5; i++) {
    Serial.print(i < bars ? "#" : " ");
  }
  Serial.print("] ");
}

const char* encTypeStr(wifi_auth_mode_t enc) {
  switch (enc) {
    case WIFI_AUTH_OPEN:            return "OPEN";
    case WIFI_AUTH_WEP:             return "WEP";
    case WIFI_AUTH_WPA_PSK:         return "WPA";
    case WIFI_AUTH_WPA2_PSK:        return "WPA2";
    case WIFI_AUTH_WPA_WPA2_PSK:    return "WPA/WPA2";
    case WIFI_AUTH_WPA3_PSK:        return "WPA3";
    case WIFI_AUTH_WPA2_WPA3_PSK:   return "WPA2/WPA3";
    case WIFI_AUTH_ENTERPRISE:      return "ENT";
    default:                        return "UNK";
  }
}

void hopChannel() {
  currentChannel++;
  if (currentChannel > 13) currentChannel = 1;
  esp_wifi_set_channel(currentChannel, WIFI_SECOND_CHAN_NONE);
}

void printSignalMap() {
  Serial.println("\r\n+----------------------------------------------+");
  Serial.println("|        WiFi Signal Strength Map              |");
  Serial.println("+----------------------------------------------+");
  for (int i = 0; i < networkCount; i++) {
    Serial.printf("| CH%-2d ", networks[i].channel);
    printRssiBar(networks[i].rssi);
    Serial.printf("%4d dBm ", networks[i].rssi);
    Serial.printf("%-5s ", encTypeStr(networks[i].encType));
    if (strlen(networks[i].ssid) > 0) {
      Serial.printf("%s", networks[i].ssid);
    } else {
      Serial.print("[Hidden]");
    }
    Serial.println();
  }
  Serial.println("+----------------------------------------------+");
}

void printChannelMap() {
  int channelPower[14] = {0};
  int channelCount[14] = {0};
  for (int i = 0; i < networkCount; i++) {
    int ch = networks[i].channel;
    if (ch >= 1 && ch <= 13) {
      channelPower[ch] += abs(networks[i].rssi);
      channelCount[ch]++;
    }
  }
  Serial.println("\r\n+----------------------------------------------+");
  Serial.println("|        Channel Occupancy Map                 |");
  Serial.println("+----------------------------------------------+");
  for (int ch = 1; ch <= 13; ch++) {
    Serial.printf("| CH%-2d |", ch);
    int blocks = channelCount[ch] * 2;
    if (blocks > 30) blocks = 30;
    for (int b = 0; b < blocks; b++) Serial.print("#");
    for (int b = blocks; b < 30; b++) Serial.print(" ");
    Serial.printf("| %d APs\r\n", channelCount[ch]);
  }
  Serial.println("+----------------------------------------------+");
}

void performScan() {
  WiFi.mode(WIFI_STA);
  WiFi.disconnect(true);
  delay(100);

  int found = WiFi.scanNetworks(false, true);
  networkCount = 0;

  for (int i = 0; i < found && networkCount < MAX_NETWORKS; i++) {
    strncpy(networks[networkCount].ssid, WiFi.SSID(i).c_str(), 32);
    networks[networkCount].ssid[32] = '\0';
    memcpy(networks[networkCount].bssid, WiFi.BSSID(i), 6);
    networks[networkCount].rssi = WiFi.RSSI(i);
    networks[networkCount].channel = WiFi.channel(i);
    networks[networkCount].encType = WiFi.encryptionType(i);
    networkCount++;
  }

  WiFi.scanDelete();
  scanCount++;

  Serial.printf("\r\n=== Scan #%d | Channel %d | %d networks found ===\r\n",
                scanCount, currentChannel, networkCount);

  printSignalMap();
  printChannelMap();
}

void setup() {
  Serial.begin(SERIAL_BAUD);
  delay(500);

  Serial.println("+----------------------------------------------+");
  Serial.println("|    W1 WiFi Scanner + Signal Mapper           |");
  Serial.println("|    Board: ESP32-C6                           |");
  Serial.println("+----------------------------------------------+");

  WiFi.mode(WIFI_STA);
  WiFi.disconnect(true);
  delay(100);

  esp_wifi_set_channel(currentChannel, WIFI_SECOND_CHAN_NONE);
  Serial.printf("Starting scan on channel %d\r\n", currentChannel);

  lastScanTime = millis();
  lastHopTime = millis();
}

void loop() {
  unsigned long now = millis();

  if (now - lastHopTime >= CHANNEL_HOP_MS) {
    hopChannel();
    lastHopTime = now;
  }

  if (now - lastScanTime >= SCAN_INTERVAL_MS) {
    performScan();
    lastScanTime = now;
  }

  delay(10);
}
