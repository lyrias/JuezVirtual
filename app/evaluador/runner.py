

import subprocess
import threading
import psutil
import time
import os
import json
import re
import ast


PROHIBITED_PATTERNS = [
    r"\bshutdown\b",
    r"\brm\s+-rf\b",
    r"\bdel\s+",
    r"\bformat\b",
    r"\bSystem\.exit\b",
    r"\bRuntime\.getRuntime\b",
    r"\bos\.system\b",
    r"\bsubprocess\b",
    r"\bProcessBuilder\b",
    r"\bfopen\s*\(.*,[\s]*['\"]w['\"]\)",
    r"\bsystem\s*\(",      
    r"#include\s*<stdlib\.h>"
]


def contains_prohibited(content: str):
    for pat in PROHIBITED_PATTERNS:
        if re.search(pat, content):
            return True, pat
    return False, ''


def analyze_python_code(source_code: str):
    try:
        tree = ast.parse(source_code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                name = ''
                if isinstance(func, ast.Attribute):
                    name = func.attr
                elif isinstance(func, ast.Name):
                    name = func.id
                if name in ('system', 'call', 'Popen', 'remove'):
                    return True, f'{name}()'
    except Exception:
        pass
    return False, ''


def analyze_java_code(source_code: str):
    try:
        import javalang
    except ImportError:
        return False, ''
    try:
        tree = javalang.parse.parse(source_code)
        for _, node in tree.filter(javalang.tree.MethodInvocation):
            if node.member in ('exec', 'exit'):
                return True, f'{node.member}()'
    except Exception:
        pass
    return False, ''


def analyze_cpp_code(source_code: str):
    patterns = [r'\bsystem\s*\(', r'\babort\s*\(']
    for pat in patterns:
        if re.search(pat, source_code):
            return True, pat
    return False, ''


def ejecutar_con_limites(cmd: list, input_path: str, output_path: str,
                         tiempo_max_ms: int, memoria_max_mb: int) -> dict:

    cmd_str = ' '.join(cmd)
    blocked, pat = contains_prohibited(cmd_str)
    if blocked:
        return {
            'exit_code': -1,
            'error': f'Patrón prohibido en comando: {pat}',
            'time_ms': 0,
            'peak_memory_mb': 0,
            'timeout': False,
            'memory_exceeded': False,
            'stderr': ''
        }

    # 2) Filtrar fuente si se pasa ruta a archivo
    for arg in cmd:
        if os.path.isfile(arg) and arg.lower().endswith(('.py', '.java', '.cpp')):
            try:
                with open(arg, 'r', encoding='utf-8', errors='ignore') as f:
                    src = f.read()
                if arg.lower().endswith('.py'):
                    blocked, pat = analyze_python_code(src)
                elif arg.lower().endswith('.java'):
                    blocked, pat = analyze_java_code(src)
                else:
                    blocked, pat = analyze_cpp_code(src)
                if blocked:
                    return {
                        'exit_code': -1,
                        'error': f'Patrón prohibido en código fuente {arg}: {pat}',
                        'time_ms': 0,
                        'peak_memory_mb': 0,
                        'timeout': False,
                        'memory_exceeded': False,
                        'stderr': ''
                    }
            except Exception as e:
                return {
                    'exit_code': -1,
                    'error': f'Error al leer {arg}: {e}',
                    'time_ms': 0,
                    'peak_memory_mb': 0,
                    'timeout': False,
                    'memory_exceeded': False,
                    'stderr': ''
                }

    # 3) Preparar ejecución y límites
    start = time.monotonic()
    timeout_sec = tiempo_max_ms / 1000.0
    peak_mem = 0
    mem_exceeded = False
    timed_out = False

    creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0

    with open(input_path, 'r', encoding='utf-8', errors='ignore') as fin, \
         open(output_path, 'w', encoding='utf-8', errors='ignore') as fout:
        proc = subprocess.Popen(
            cmd,
            stdin=fin,
            stdout=fout,
            stderr=subprocess.PIPE,
            creationflags=creationflags
        )
        ps_proc = psutil.Process(proc.pid)

        def monitor():
            nonlocal peak_mem, mem_exceeded
            while proc.poll() is None:
                try:
                    mem = ps_proc.memory_info().rss // (1024 * 1024)
                    if mem > peak_mem:
                        peak_mem = mem
                    if peak_mem > memoria_max_mb:
                        ps_proc.terminate()
                        mem_exceeded = True
                        break
                except psutil.NoSuchProcess:
                    break
                time.sleep(0.1)

        t = threading.Thread(target=monitor, daemon=True)
        t.start()

        try:
            proc.wait(timeout=timeout_sec)
        except subprocess.TimeoutExpired:
            proc.terminate()
            timed_out = True

        t.join()
        exit_code = proc.returncode
        elapsed_ms = int((time.monotonic() - start) * 1000)
        stderr = proc.stderr.read().decode('utf-8', errors='ignore')

    return {
        'exit_code': exit_code,
        'time_ms': elapsed_ms,
        'peak_memory_mb': peak_mem,
        'timeout': timed_out,
        'memory_exceeded': mem_exceeded,
        'stderr': stderr
    }

def obtener_veredicto(resultado, ruta_esperada, ruta_usuario, tolerancia=True):

    if 'error' in resultado:
        return 'CE'

    if resultado.get('timeout', False):
        return 'TLE'

    if resultado.get('memory_exceeded', False):
        return 'MLE'

    if resultado.get('exit_code', 0) != 0:
        return 'RE'

    try:
        with open(ruta_esperada, 'r', encoding='utf-8') as f1, \
             open(ruta_usuario, 'r', encoding='utf-8') as f2:
            salida_esperada = f1.read().rstrip('\r\n')
            salida_usuario = f2.read().rstrip('\r\n')
    except Exception:
        return 'IE'

    if salida_esperada == salida_usuario:
        return 'AC'

    if not tolerancia:
        return 'WA'

    def normalizar(linea):
        return ' '.join(linea.strip().split())

    esperado = [normalizar(l) for l in salida_esperada.splitlines()]
    usuario = [normalizar(l) for l in salida_usuario.splitlines()]

    if esperado == usuario:
        return 'PE'  
    else:
        return 'WA'  

if __name__ == '__main__':
    resultado = ejecutar_con_limites(
        cmd=['python', 'data_problemas/A1001/main.py'],
        input_path='data_problemas/A1001/entradas.txt',
        output_path='data_problemas/A1001/salida_temp.txt',
        tiempo_max_ms=1000,
        memoria_max_mb=128
    )
    print(json.dumps(resultado, indent=2))
    veredicto = obtener_veredicto(resultado, 'data_problemas/A1001/salidas.txt', 'data_problemas/A1001/salida_temp.txt')
    print("Veredicto:", veredicto)