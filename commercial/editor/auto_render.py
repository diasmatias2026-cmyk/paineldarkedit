"""Select the fastest working encoder using the actual composition, not GPU branding."""
import json,subprocess,time,tempfile
from pathlib import Path
from engine import command
from runtime import capture
ENCODERS=['libx264','h264_amf','h264_nvenc','h264_qsv']
LABELS={'libx264':'CPU','h264_amf':'GPU AMD','h264_nvenc':'GPU NVIDIA','h264_qsv':'GPU Intel'}
def choose_encoder(source,artwork,values,folder,cancel_check=lambda:False):
    measurements=[]
    with tempfile.TemporaryDirectory(prefix='benchmark_',dir=folder) as directory:
        for encoder in ENCODERS:
            if cancel_check():raise RuntimeError('Teste cancelado.')
            output=Path(directory)/(encoder+'.mp4')
            args=command(source,output,artwork,{**values,'_encoder':encoder})
            args[-1:-1]=['-t','0.8','-frames:v','24']
            started=time.perf_counter()
            try:
                result=capture(args,timeout=25,cancel_check=cancel_check)
                passed=result.returncode==0 and output.is_file() and output.stat().st_size>1000
                error=result.stderr.decode('utf-8',errors='replace')[-1800:] if not passed else ''
            except TimeoutError:passed=False;error='Tempo de teste excedido.'
            measurements.append(dict(encoder=encoder,available=passed,seconds=round(time.perf_counter()-started,3),error=error))
    valid=[m for m in measurements if m['available']]
    if not valid:raise RuntimeError('Nenhum encoder conseguiu renderizar o teste. Consulte o diagnóstico.')
    chosen=min(valid,key=lambda m:m['seconds'])['encoder']
    Path(folder,'benchmark-encoders.json').write_text(json.dumps({'selected':chosen,'samples':measurements},indent=2,ensure_ascii=False),encoding='utf-8')
    return chosen
