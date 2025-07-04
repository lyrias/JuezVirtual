from flask import Flask, render_template, jsonify
from threading import Thread, Lock
import time

app = Flask(__name__)

cola_lock = Lock()
pendientes = []
en_ejecucion = []
finalizados = []
envio_id_counter = 1

def worker_simulado():
    global pendientes, en_ejecucion, finalizados, envio_id_counter

    last_insert_time = time.time()

    while True:
        now = time.time()

        if now - last_insert_time >= 6:
            with cola_lock:
                pendientes.append({
                    "id": envio_id_counter,
                    "usuario": f"user{envio_id_counter}",
                    "problema": f"P{envio_id_counter}"
                })
                print(f"[+] Envío #{envio_id_counter} agregado a pendientes")
                envio_id_counter += 1
            last_insert_time = now

        if not en_ejecucion:
            with cola_lock:
                if pendientes:
                    envio = pendientes.pop(0)
                    en_ejecucion.append(envio)
                    print(f"[~] Envío #{envio['id']} movido a en_ejecucion")

            time.sleep(10)

            with cola_lock:
                if en_ejecucion:
                    envio = en_ejecucion.pop(0)
                    finalizados.append(envio)
                    print(f"[✓] Envío #{envio['id']} movido a finalizados")
        else:
            time.sleep(1)

@app.route("/")
def index():
    return render_template("simulacion.html")

@app.route("/cola_estado")
def cola_estado():
    with cola_lock:
        return jsonify({
            "pendientes": pendientes.copy(),
            "en_ejecucion": en_ejecucion.copy(),
            "finalizados": finalizados.copy()
        })

if __name__ == "__main__":
    hilo = Thread(target=worker_simulado, daemon=True)
    hilo.start()
    app.run(debug=True)
