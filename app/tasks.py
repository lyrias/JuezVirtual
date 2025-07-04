import os
from datetime import datetime
from app import create_app, db
from app.models import Envio, Veredicto
from app.mi_evaluador import evaluar_codigo
import json 

app = create_app()

def procesar_envio(envio_id):
    with app.app_context():
        envio = db.session.get(Envio, envio_id)
        if not envio:
            print(f"[ERROR] Envío {envio_id} no encontrado.")
            return

        problema = envio.problema
        lenguaje = envio.lenguaje

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # app/
        carpeta_problema = os.path.join(BASE_DIR, 'data_problemas', problema.codigo)
        carpeta_envio = os.path.join(carpeta_problema, f'envio_{envio.id}')
        ruta_fuente = os.path.join(carpeta_envio, f"main{lenguaje.extension_archivo}")

        print(f"[INFO] Evaluando envío {envio_id} en {ruta_fuente}...")
        print("[DEBUG] Parámetros usados:")
        print(f"  carpeta_problema: {carpeta_problema}")
        print(f"  carpeta_envio: {carpeta_envio}")
        print(f"  ruta_fuente: {ruta_fuente}")
        print(f"  tiempo_ms: {problema.limite_tiempo * 1000}")
        print(f"  memoria_mb: {problema.limite_memoria}")

        resultado = evaluar_codigo(
            ruta_fuente=ruta_fuente,
            carpeta_envio=carpeta_envio,
            carpeta_problema=carpeta_problema,
            tiempo_ms=int(problema.limite_tiempo * 1000),
            memoria_mb=problema.limite_memoria,
            tolerancia=True
        )

        print("[DEBUG] Resultado completo:")
        print(json.dumps(resultado, indent=2))

        veredicto = Veredicto.query.filter_by(codigo=resultado.get('veredicto')).first()
        envio.veredicto_id = veredicto.id if veredicto else None
        envio.tiempo_ejecucion = resultado.get("time_ms", 0) / 1000
        envio.memoria_usada = resultado.get("peak_memory_mb", 0)
        envio.enviado_en = datetime.now()

        db.session.commit()

        print(f"[INFO] Evaluación terminada. Veredicto: {resultado.get('veredicto')}")
        return resultado
