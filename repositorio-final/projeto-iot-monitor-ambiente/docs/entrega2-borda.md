# Entrega 2 – Protótipo de Borda e Ingestão de Dados

## 1. O que foi feito

- **Firmware** do ESP32 (`firmware/sketch.ino`) rodando no simulador Wokwi.
- **Sensor DHT22** lendo temperatura e umidade.
- **LED** representando o ventilador (atuador).
- **Transmissão via MQTT** para o broker público `broker.hivemq.com`.
- **Banco de dados SQLite** recebendo e guardando cada leitura (`backend/app.py`).

## 2. O circuito

| Peça | Pino da peça | Ligado no ESP32 |
|---|---|---|
| DHT22 | VCC (energia) | 3V3 |
| DHT22 | GND (terra) | GND |
| DHT22 | SDA (dados) | Pino 15 |
| LED | Perna + (via resistor 220Ω) | Pino 2 |
| LED | Perna − | GND |

O resistor serve para o LED não "queimar" (limita a corrente).

## 3. Como o ESP32 funciona (passo a passo)

1. **Liga** e conecta no Wi-Fi virtual `Wokwi-GUEST`.
2. **Conecta** no broker MQTT (o "carteiro").
3. **Se inscreve** no tópico de comandos (fica "esperando cartas" com ordens).
4. **A cada 5 segundos:** lê o sensor e envia uma mensagem assim:
   ```json
   {"temp": 26.0, "umid": 55.0}
   ```
5. **Se chegar "ON"** → acende o LED. **Se chegar "OFF"** → apaga.

## 4. Os tópicos MQTT ("endereços" das mensagens)

| Tópico | Quem envia | Quem recebe | Conteúdo |
|---|---|---|---|
| `ads-iot-monitor-7391/telemetria` | ESP32 | Servidor | `{"temp": 26.0, "umid": 55.0}` |
| `ads-iot-monitor-7391/comando` | Servidor | ESP32 | `ON` ou `OFF` |

O número `7391` só existe para nosso endereço não se misturar com o de outras pessoas que usam o mesmo broker público.

## 5. O banco de dados

Uma única tabela, chamada `leituras`:

| Coluna | Tipo | Exemplo | Significado |
|---|---|---|---|
| `id` | INTEGER (automático) | 1 | Número da leitura |
| `data_hora` | TEXT | 2026-11-11 14:30:05 | Quando chegou |
| `temperatura` | REAL | 26.0 | Em °C |
| `umidade` | REAL | 55.0 | Em % |

```sql
CREATE TABLE leituras (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    data_hora   TEXT NOT NULL,
    temperatura REAL NOT NULL,
    umidade     REAL NOT NULL
);
```

## 6. Como comprovar que funciona

1. Rode o `app.py` (ver README).
2. Dê Play no Wokwi.
3. No terminal do `app.py` aparece a cada 5 s:
   ```
   [2026-11-11 14:30:05] Salvo: {'temp': 26.0, 'umid': 55.0}
   ```
4. O arquivo `backend/dados.db` é criado e cresce. Para olhar dentro dele, use o programa gratuito [DB Browser for SQLite](https://sqlitebrowser.org/).

> 📸 **Para a entrega:** tire print do Wokwi rodando + terminal do `app.py` mostrando "Salvo" + a tabela no DB Browser.
