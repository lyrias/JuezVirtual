import os
import platform

def apagar_maquina():
    sistema = platform.system()
    if sistema == "Windows":
        os.system("shutdown /s /t 0")
    elif sistema == "Linux" or sistema == "Darwin":  
        os.system("sudo shutdown -h now")
    else:
        print(f"Sistema operativo {sistema} no soportado para apagado automático.")

if __name__ == "__main__":
    apagar_maquina()
