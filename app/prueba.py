from mi_evaluador import evaluar_codigo
import os
import json

tiempo_ms = 2000   
memoria_mb = 1024  

carpeta_problema = 'data_problemas/A1001'
carpeta_envio = os.path.join(carpeta_problema, 'envio_25')
ruta_fuente = os.path.join(carpeta_envio, 'main.py') 

res_py = evaluar_codigo(
    ruta_fuente=ruta_fuente,
    carpeta_envio=carpeta_envio,
    carpeta_problema=carpeta_problema,
    tiempo_ms=tiempo_ms,
    memoria_mb=memoria_mb,
    tolerancia=True
)

print("Python:", json.dumps(res_py, indent=2))

