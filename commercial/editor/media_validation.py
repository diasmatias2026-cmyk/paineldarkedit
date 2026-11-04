"""Validate content before registering an upload; no external media protocols."""
import re
from pathlib import Path
from engine import FFMPEG
from runtime import INPUT_FLAGS,capture
IMAGES={'.jpg','.jpeg','.png','.webp','.bmp'}
def inspect(path):
    result=capture([str(FFMPEG),'-hide_banner','-nostdin']+INPUT_FLAGS+['-i',str(path),'-map','0:v:0','-frames:v','1','-an','-f','null','-'],timeout=25)
    text=result.stderr.decode('utf-8',errors='replace')
    match=re.search(r'Video:.*? (\d{2,5})x(\d{2,5})',text)
    if result.returncode or not match:raise ValueError('Arquivo inválido ou formato de vídeo/imagem não suportado.')
    width,height=map(int,match.groups())
    if width*height>20000000 or max(width,height)>8192:raise ValueError('A mídia excede o limite seguro de resolução (20 megapixels / 8192 px).')
    duration=0
    found=re.search(r'Duration: (\d+):(\d+):([\d.]+)',text)
    if found:duration=int(found[1])*3600+int(found[2])*60+float(found[3])
    if duration>7200:raise ValueError('Escolha vídeos de até duas horas por arquivo.')
    return {'width':width,'height':height,'duration':duration,'image':Path(path).suffix.lower() in IMAGES}
def normalize_asset(path):
    output=Path(path).with_name(Path(path).stem+'_safe.png')
    result=capture([str(FFMPEG),'-hide_banner','-loglevel','error','-nostdin','-n']+INPUT_FLAGS+['-i',str(path),'-frames:v','1','-vf','scale=1080:1920:force_original_aspect_ratio=decrease','-update','1',str(output)],timeout=25)
    if result.returncode:output.unlink(missing_ok=True);raise ValueError('Não foi possível preparar a imagem do template.')
    return output
