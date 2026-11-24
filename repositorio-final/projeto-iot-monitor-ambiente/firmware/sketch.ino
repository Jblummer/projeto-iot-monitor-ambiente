/*
  MONITOR DE AMBIENTE - ESP32 (simulado no Wokwi)

  O que este código faz, em português simples:
  1. Conecta o ESP32 na internet (Wi-Fi).
  2. Conecta no "carteiro" da internet (broker MQTT).
  3. A cada 5 segundos lê a temperatura e a umidade e envia.
  4. Fica escutando ordens ("ON" ou "OFF") para ligar/desligar o ventilador (LED).
*/

#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>

// ---------- CONFIGURAÇÕES ----------
const char* WIFI_NOME  = "Wokwi-GUEST";        // Wi-Fi virtual do Wokwi (sem senha)
const char* WIFI_SENHA = "";
const char* BROKER     = "broker.hivemq.com";   // "carteiro" público e gratuito
const int   PORTA      = 1883;

// Tópicos = "endereços" das mensagens. Precisam ser IGUAIS aos do app.py
const char* TOPICO_DADOS   = "ads-iot-monitor-7391/telemetria";
const char* TOPICO_COMANDO = "ads-iot-monitor-7391/comando";

#define PINO_SENSOR     15   // DHT22 ligado no pino 15
#define PINO_VENTILADOR 2    // LED (representa o ventilador) no pino 2

// ---------- OBJETOS ----------
DHT sensor(PINO_SENSOR, DHT22);
WiFiClient wifi;
PubSubClient mqtt(wifi);
unsigned long ultimoEnvio = 0;

// Chamado automaticamente quando chega uma ordem do site
void recebeuComando(char* topico, byte* conteudo, unsigned int tamanho) {
  String ordem = "";
  for (unsigned int i = 0; i < tamanho; i++) ordem += (char)conteudo[i];

  if (ordem == "ON") {
    digitalWrite(PINO_VENTILADOR, HIGH);
    Serial.println("Ventilador LIGADO");
  } else if (ordem == "OFF") {
    digitalWrite(PINO_VENTILADOR, LOW);
    Serial.println("Ventilador DESLIGADO");
  }
}

void conectarMQTT() {
  while (!mqtt.connected()) {
    Serial.print("Conectando ao broker MQTT... ");
    String id = "esp32-" + String(random(0xffff), HEX);
    if (mqtt.connect(id.c_str())) {
      Serial.println("OK!");
      mqtt.subscribe(TOPICO_COMANDO);
    } else {
      Serial.println("falhou, tentando de novo em 2s");
      delay(2000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(PINO_VENTILADOR, OUTPUT);
  sensor.begin();

  Serial.print("Conectando ao Wi-Fi");
  WiFi.begin(WIFI_NOME, WIFI_SENHA);
  while (WiFi.status() != WL_CONNECTED) { delay(300); Serial.print("."); }
  Serial.println(" OK!");

  mqtt.setServer(BROKER, PORTA);
  mqtt.setCallback(recebeuComando);
}

void loop() {
  if (!mqtt.connected()) conectarMQTT();
  mqtt.loop();  // verifica se chegou alguma ordem

  if (millis() - ultimoEnvio > 5000) {   // a cada 5 segundos
    ultimoEnvio = millis();
    float temp = sensor.readTemperature();
    float umid = sensor.readHumidity();
    if (isnan(temp) || isnan(umid)) { Serial.println("Erro ao ler sensor"); return; }

    char mensagem[64];
    snprintf(mensagem, sizeof(mensagem), "{\"temp\": %.1f, \"umid\": %.1f}", temp, umid);
    mqtt.publish(TOPICO_DADOS, mensagem);
    Serial.print("Enviado: "); Serial.println(mensagem);
  }
}
