"""
MONITOR DE AMBIENTE - Servidor (backend)

O que este arquivo faz, em português simples:
1. Escuta as mensagens que o ESP32 manda (temperatura e umidade).
2. Guarda cada leitura no banco de dados (arquivo dados.db).
3. Mostra o site (dashboard) no endereço http://localhost:5000
4. Quando alguém clica em "Ligar/Desligar", manda a ordem para o ESP32.
"""
import json
import sqlite3
from datetime import datetime

import paho.mqtt.client as mqtt
from flask import Flask, jsonify, render_template, request

# ---------- CONFIGURAÇÕES (iguais às do sketch.ino) ----------
BROKER = "broker.hivemq.com"
TOPICO_DADOS = "ads-iot-monitor-7391/telemetria"
TOPICO_COMANDO = "ads-iot-monitor-7391/comando"
BANCO = "dados.db"

estado_ventilador = "OFF"  # lembra o último comando enviado


# ---------- BANCO DE DADOS ----------
def conectar_banco():
    return sqlite3.connect(BANCO)


def criar_tabela():
    with conectar_banco() as banco:
        banco.execute("""
            CREATE TABLE IF NOT EXISTS leituras (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                data_hora   TEXT NOT NULL,
                temperatura REAL NOT NULL,
                umidade     REAL NOT NULL
            )
        """)


# ---------- MQTT (conversa com o ESP32) ----------
def ao_conectar(cliente, userdata, flags, codigo, propriedades):
    print("Conectado ao broker MQTT! Aguardando dados do ESP32...")
    cliente.subscribe(TOPICO_DADOS)


def ao_receber_mensagem(cliente, userdata, msg):
    try:
        dados = json.loads(msg.payload.decode())
        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with conectar_banco() as banco:
            banco.execute(
                "INSERT INTO leituras (data_hora, temperatura, umidade) VALUES (?, ?, ?)",
                (agora, dados["temp"], dados["umid"]),
            )
        print(f"[{agora}] Salvo: {dados}")
    except Exception as erro:
        print("Mensagem inválida ignorada:", erro)


cliente_mqtt = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
cliente_mqtt.on_connect = ao_conectar
cliente_mqtt.on_message = ao_receber_mensagem


# ---------- SITE (Flask) ----------
app = Flask(__name__)


@app.route("/")
def pagina_inicial():
    return render_template("index.html")


@app.route("/api/leituras")
def ultimas_leituras():
    with conectar_banco() as banco:
        linhas = banco.execute(
            "SELECT data_hora, temperatura, umidade FROM leituras ORDER BY id DESC LIMIT 50"
        ).fetchall()
    linhas.reverse()  # mais antiga primeiro (para o gráfico)
    return jsonify({
        "leituras": [{"data_hora": d, "temp": t, "umid": u} for d, t, u in linhas],
        "ventilador": estado_ventilador,
    })


@app.route("/api/comando", methods=["POST"])
def enviar_comando():
    global estado_ventilador
    ordem = request.json.get("comando")
    if ordem not in ("ON", "OFF"):
        return jsonify({"erro": "Use ON ou OFF"}), 400
    cliente_mqtt.publish(TOPICO_COMANDO, ordem)
    estado_ventilador = ordem
    return jsonify({"ok": True, "ventilador": ordem})


if __name__ == "__main__":
    criar_tabela()
    cliente_mqtt.connect(BROKER, 1883)
    cliente_mqtt.loop_start()  # MQTT roda "em segundo plano"
    print("Abra no navegador: http://localhost:5000")
    app.run(port=5000)
