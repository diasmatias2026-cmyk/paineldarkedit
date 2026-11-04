"""Bounded, cancellable subprocesses for local-only media processing."""
import subprocess,threading,time,queue,os,ctypes
PROCESSES=set();LOCK=threading.Lock();SLOTS=threading.BoundedSemaphore(3)
INPUT_FLAGS=['-protocol_whitelist','file,pipe','-format_whitelist','mov,matroska,webm,image2,png_pipe,jpeg_pipe,webp_pipe,bmp_pipe']
JOB=None

def spawn(args,**kwargs):
    process=subprocess.Popen(args,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),**kwargs)
    with LOCK:PROCESSES.add(process)
    if JOB:
        try:ctypes.windll.kernel32.AssignProcessToJobObject(JOB,int(process._handle))
        except Exception:pass
    return process

def stop(process):
    if process.poll() is None:
        process.terminate()
        try:process.wait(timeout=2)
        except subprocess.TimeoutExpired:process.kill();process.wait(timeout=3)

def finish(process):
    with LOCK:PROCESSES.discard(process)

def terminate_all():
    with LOCK:processes=list(PROCESSES)
    for process in processes:
        try:stop(process)
        except OSError:pass

def capture(args,timeout=25,cancel_check=lambda:False):
    if not SLOTS.acquire(timeout=2):raise RuntimeError('O processamento está ocupado. Aguarde e tente novamente.')
    process=None
    try:
        process=spawn(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        started=time.monotonic()
        while True:
            if cancel_check():stop(process);raise RuntimeError('Operação cancelada.')
            if time.monotonic()-started>timeout:stop(process);raise TimeoutError('Tempo máximo de análise excedido.')
            try:
                stdout,stderr=process.communicate(timeout=.2)
                return subprocess.CompletedProcess(args,process.returncode,stdout,stderr)
            except subprocess.TimeoutExpired:pass
    finally:
        if process:stop(process);finish(process)
        SLOTS.release()

def progress(args,log,on_progress=None,cancel_check=lambda:False,process_callback=None):
    events=queue.Queue();last=time.monotonic();started=last
    with open(log,'a',encoding='utf-8') as stream:
        process=spawn(args,stdout=subprocess.PIPE,stderr=stream,text=True,encoding='utf-8',errors='replace',bufsize=1)
        if process_callback:process_callback(process)
        def read():
            for line in process.stdout:events.put(line.strip())
            events.put(None)
        reader=threading.Thread(target=read,daemon=True);reader.start()
        try:
            while True:
                if cancel_check():stop(process);raise RuntimeError('Exportação cancelada.')
                if time.monotonic()-last>180 or time.monotonic()-started>86400:
                    stop(process);raise RuntimeError('Renderização sem progresso. O processo foi encerrado com segurança.')
                try:line=events.get(timeout=.2)
                except queue.Empty:
                    if process.poll() is not None and not reader.is_alive():break
                    continue
                if line is None:break
                last=time.monotonic()
                if line.startswith('out_time_us='):
                    try:
                        if on_progress:on_progress(max(0,int(line.split('=',1)[1])/1e6))
                    except ValueError:pass
            return process.wait(timeout=5)
        finally:
            stop(process);finish(process);process.stdout.close()

def install_job_guard():
    """Best effort kill-on-close Job Object; explicit registry cleanup is always active."""
    global JOB
    if os.name!='nt':return
    from ctypes import wintypes
    class Basic(ctypes.Structure):
        _fields_=[('ProcessTime',ctypes.c_int64),('JobTime',ctypes.c_int64),('LimitFlags',wintypes.DWORD),('MinWS',ctypes.c_size_t),('MaxWS',ctypes.c_size_t),('Active',wintypes.DWORD),('Affinity',ctypes.c_size_t),('Priority',wintypes.DWORD),('Scheduling',wintypes.DWORD)]
    class IO(ctypes.Structure):_fields_=[('ReadOps',ctypes.c_uint64),('WriteOps',ctypes.c_uint64),('OtherOps',ctypes.c_uint64),('ReadBytes',ctypes.c_uint64),('WriteBytes',ctypes.c_uint64),('OtherBytes',ctypes.c_uint64)]
    class Extended(ctypes.Structure):_fields_=[('Basic',Basic),('IO',IO),('ProcessMemory',ctypes.c_size_t),('JobMemory',ctypes.c_size_t),('PeakProcess',ctypes.c_size_t),('PeakJob',ctypes.c_size_t)]
    kernel=ctypes.windll.kernel32;kernel.CreateJobObjectW.restype=wintypes.HANDLE
    kernel.SetInformationJobObject.argtypes=[wintypes.HANDLE,ctypes.c_int,ctypes.c_void_p,wintypes.DWORD]
    kernel.AssignProcessToJobObject.argtypes=[wintypes.HANDLE,wintypes.HANDLE]
    handle=kernel.CreateJobObjectW(None,None);limits=Extended();limits.Basic.LimitFlags=0x2000|0x100;limits.ProcessMemory=4*1024**3
    if handle and kernel.SetInformationJobObject(handle,9,ctypes.byref(limits),ctypes.sizeof(limits)):JOB=handle
