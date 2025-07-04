from threading import Thread
import time
from app.cola_envios import cola_envios


_hilo_iniciado = False

def procesar_envios():
    from app.tasks import procesar_envio  
    
    while True:
        envio_id = cola_envios.get()
        try:
            procesar_envio(envio_id)
        except Exception as e:
            print(f"[ERROR] Error al evaluar envío {envio_id}: {e}")
        finally:
            cola_envios.task_done()  
        time.sleep(5)


def iniciar_worker():
    global _hilo_iniciado
    if not _hilo_iniciado:
        hilo = Thread(target=procesar_envios, daemon=True)
        hilo.start()
        _hilo_iniciado = True
        print("[WORKER] Hilo iniciado correctamente.")
