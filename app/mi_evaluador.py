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
                if isinstance(func, ast.Attribute): name = func.attr
                elif isinstance(func, ast.Name): name = func.id
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
    for pat in [r'\bsystem\s*\(', r'\babort\s*\(']:
        if re.search(pat, source_code): return True, pat
    return False, ''

def compilar_fuente(ruta_fuente: str) -> dict:
    """
    Compila Java o C++ si corresponde; Python no requiere compilación.
    Retorna {'success': bool, 'stderr': str}.
    """
    ext = ruta_fuente.lower().split('.')[-1]
    carpeta = os.path.dirname(ruta_fuente)
    if ext == 'py':
        return {'success': True, 'stderr': ''}
    if ext == 'java':
        cmd = ['javac', ruta_fuente]
    elif ext == 'cpp':
        exe = ruta_fuente[:-4] + ('.exe' if os.name=='nt' else '')
        cmd = ['g++', '-std=c++17', ruta_fuente, '-o', exe]
    else:
        return {'success': False, 'stderr': f'Extensión no soportada: .{ext}'}
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)
        if proc.returncode != 0:
            return {'success': False, 'stderr': proc.stderr.decode('utf-8', errors='ignore')}
    except Exception as e:
        return {'success': False, 'stderr': str(e)}
    return {'success': True, 'stderr': ''}

def ejecutar_con_limites(cmd: list, input_path: str, output_path: str,
                         tiempo_max_ms: int, memoria_max_mb: int) -> dict:
    cmd_str = ' '.join(cmd)
    blocked, pat = contains_prohibited(cmd_str)
    if blocked:
        return {'exit_code': -1, 'error': f'Patrón prohibido en comando: {pat}',
                'time_ms':0,'peak_memory_mb':0,'timeout':False,'memory_exceeded':False,'stderr':''}
    for arg in cmd:
        if os.path.isfile(arg) and arg.lower().endswith(('.py','.java','.cpp')):
            with open(arg,'r',errors='ignore') as f: src=f.read()
            if arg.endswith('.py'): failed, pat = analyze_python_code(src)
            elif arg.endswith('.java'): failed, pat = analyze_java_code(src)
            else: failed, pat = analyze_cpp_code(src)
            if failed:
                return {'exit_code': -1, 'error':f'Patrón peligroso en {arg}: {pat}',
                        'time_ms':0,'peak_memory_mb':0,'timeout':False,'memory_exceeded':False,'stderr':''}
    start = time.monotonic(); timeout_sec=tiempo_max_ms/1000.0
    peak_mem=0; mem_ex=False; timed_out=False
    flags = subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
    with open(input_path,'r',errors='ignore') as fin, open(output_path,'w',errors='ignore') as fout:
        proc = subprocess.Popen(cmd, stdin=fin, stdout=fout, stderr=subprocess.PIPE, creationflags=flags)
        ps_proc = psutil.Process(proc.pid)
        def mon():
            nonlocal peak_mem,mem_ex
            while proc.poll() is None:
                try:
                    m=ps_proc.memory_info().rss//(1024*1024)
                    if m>peak_mem: peak_mem=m
                    if m>memoria_max_mb:
                        ps_proc.terminate(); mem_ex=True; break
                except psutil.NoSuchProcess: break
                time.sleep(0.1)
        t=threading.Thread(target=mon,daemon=True); t.start()
        try: proc.wait(timeout=timeout_sec)
        except subprocess.TimeoutExpired: proc.terminate(); timed_out=True
        t.join()
        code=proc.returncode; elapsed=int((time.monotonic()-start)*1000)
        err=proc.stderr.read().decode(errors='ignore')
    return {'exit_code':code,'time_ms':elapsed,'peak_memory_mb':peak_mem,'timeout':timed_out,
            'memory_exceeded':mem_ex,'stderr':err}

def obtener_veredicto(resultado: dict, ruta_esperada: str, ruta_usuario: str, tolerancia=True) -> str:
    if 'error' in resultado: return 'CE'
    if resultado.get('timeout'): return 'TLE'
    if resultado.get('memory_exceeded'): return 'MLE'
    if resultado.get('exit_code',0)!=0: return 'RE'
    try:
        with open(ruta_esperada,'r',encoding='utf-8') as f1, open(ruta_usuario,'r', encoding='utf-8') as f2:
            exp=f1.read().rstrip('\r\n'); usr=f2.read().rstrip('\r\n')
    except: return 'IE'
    if exp==usr: return 'AC'
    if not tolerancia: return 'WA'
    def norm(l): return ' '.join(l.strip().split())
    if [norm(l) for l in exp.splitlines()]==[norm(l) for l in usr.splitlines()]: return 'PE'
    return 'WA'
    
def evaluar_codigo(ruta_fuente: str, carpeta_envio: str, carpeta_problema: str, tiempo_ms: int, memoria_mb: int, tolerancia=True) -> dict:
    comp = compilar_fuente(ruta_fuente)
    if not comp['success']:
        return {
            'exit_code': -1,
            'time_ms': 0,
            'peak_memory_mb': 0,
            'timeout': False,
            'memory_exceeded': False,
            'stderr': comp['stderr'],
            'veredicto': 'CE'
        }

    ext = ruta_fuente.lower().split('.')[-1]
    if ext == 'py':
        cmd = ['python', ruta_fuente]
    elif ext == 'java':
        cls = os.path.splitext(os.path.basename(ruta_fuente))[0]
        cmd = ['java', '-cp', carpeta_envio, cls]
    elif ext == 'cpp':
        exe = ruta_fuente[:-4] + ('.exe' if os.name == 'nt' else '')
        cmd = [exe]
    else:
        return {
            'exit_code': -1,
            'error': 'Extensión no soportada',
            'time_ms': 0,
            'peak_memory_mb': 0,
            'timeout': False,
            'memory_exceeded': False,
            'stderr': '',
            'veredicto': 'IE'
        }

    inp = os.path.abspath(os.path.join(carpeta_problema, 'entradas.txt'))
    out = os.path.abspath(os.path.join(carpeta_envio, 'salida_temp.txt'))
    salida_esperada = os.path.abspath(os.path.join(carpeta_problema, 'salidas.txt'))

    if not os.path.exists(inp) or not os.path.exists(salida_esperada):
        return {
            'exit_code': -1,
            'time_ms': 0,
            'peak_memory_mb': 0,
            'timeout': False,
            'memory_exceeded': False,
            'stderr': 'Archivo de prueba no encontrado',
            'veredicto': 'IE'
        }

    res = ejecutar_con_limites(cmd, inp, out, tiempo_ms, memoria_mb)
    res['veredicto'] = obtener_veredicto(res, salida_esperada, out, tolerancia)

    return res
