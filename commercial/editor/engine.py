"""Local deterministic template renderer. Never overwrites source media."""
from pathlib import Path
import json
import subprocess
import re
import io
import os
import sys
from PIL import Image, ImageDraw, ImageFont, ImageOps
from runtime import INPUT_FLAGS, capture, progress
Image.MAX_IMAGE_PIXELS=20000000

ROOT = Path(__file__).resolve().parent
FFMPEG = ROOT / 'tools' / 'ffmpeg.exe'
DATA_ROOT = Path(os.environ.get('DARKEDIT_DATA_DIR', str(Path(os.environ.get('LOCALAPPDATA',str(Path.home()/'.local/share')))/'DarkEditCommercial') if getattr(sys,'frozen',False) else str(ROOT)))
DEFAULT = dict(name='Meu perfil', handle='@meuperfil', title='Sua chamada aqui', background='#ffffff', x=70, y=750, width=940, height=770, seconds=8, fit='cover', radius=48, crop_top=0, crop_bottom=0, crop_left=0, crop_right=0, zoom=1, shift_x=0, shift_y=0, erase_placeholder=False, erase_box=None, template='', avatar='')

def detect_template_window(path):
    """Recognize this Canva placeholder; never guess windows on unrelated artwork."""
    with Image.open(path) as source:
        image = source.convert('RGB').resize((1080, 1920))
    from PIL import ImageChops
    mask = ImageChops.difference(image, Image.new('RGB', image.size, (241, 241, 244))).convert('L').point(lambda p: 255 if p < 4 else 0)
    rows = [y for y in range(1920) if mask.crop((0,y,1080,y+1)).histogram()[255] > 500]
    if not rows: return None
    top, bottom = max(0,min(rows)-25), min(1920,max(rows)+26)
    box = mask.crop((0,top,1080,bottom)).getbbox()
    if not box: return None
    left, offset_top, right, offset_bottom = box
    bottom = top + offset_bottom
    top += offset_top
    if right-left < 500 or bottom-top < 400 or mask.histogram()[255] < 200000: return None
    return dict(x=round((left+2)/10)*10, y=round((top+2)/10)*10, width=round((right-left-4)/10)*10, height=round((bottom-top-4)/10)*10, radius=48, erase_placeholder=True, background='#ffffff', fit='cover')

def config(values):
    c = {**DEFAULT, **values}
    for k in ['x', 'y', 'width', 'height']:
        c[k] = int(c[k])
    if c['width'] < 32 or c['height'] < 32 or min(c['x'], c['y']) < 0 or c['x'] + c['width'] > 1080 or c['y'] + c['height'] > 1920:
        raise ValueError('A janela da mídia precisa caber no quadro de 1080 × 1920.')
    c['width'] -= c['width'] % 2
    c['height'] -= c['height'] % 2
    for key, low, high in [('zoom',0.25,4),('shift_x',-100,100),('shift_y',-100,100)]:
        c[key] = float(c[key])
        if not low <= c[key] <= high: raise ValueError('Enquadramento fora do limite: '+key)
    for key in ['crop_top','crop_bottom','crop_left','crop_right']:
        c[key]=float(c[key])
        if not 0 <= c[key] <= 90: raise ValueError('Recorte inválido.')
    if c['crop_top']+c['crop_bottom']>90 or c['crop_left']+c['crop_right']>90: raise ValueError('Preserve pelo menos 10% da mídia no recorte.')
    c['seconds'] = float(c['seconds'])
    if not 1 <= c['seconds'] <= 600:
        raise ValueError('Duração da imagem: entre 1 e 600 segundos.')
    if not re.fullmatch(r'#[0-9a-fA-F]{6}', c['background']):
        raise ValueError('Cor deve ser hexadecimal, por exemplo #efedf5.')
    if c['fit'] not in ['contain', 'cover']:
        raise ValueError('Encaixe inválido.')
    return c

def font(size):
    for path in ['C:/Windows/Fonts/segoeui.ttf', 'C:/Windows/Fonts/arial.ttf']:
        if Path(path).is_file():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def wrap(text, draw, f, width):
    lines = []
    for paragraph in str(text).splitlines() or ['']:
        line = ''
        for word in paragraph.split():
            candidate = (line + ' ' + word).strip()
            if draw.textlength(candidate, font=f) > width and line:
                lines.append(line)
                line = word
            else:
                line = candidate
        lines.append(line)
    return lines

def overlay(values):
    c = config(values)
    if c['template']:
        with Image.open(c['template']) as src:
            image = src.convert('RGBA').resize((1080, 1920), Image.Resampling.LANCZOS)
    else:
        image = Image.new('RGBA', (1080, 1920), c['background'])
    draw = ImageDraw.Draw(image)
    if not c['template']:
        draw.ellipse((110, 245, 286, 421), fill='#d2d8d0')
        if c['avatar']:
            with Image.open(c['avatar']) as src:
                avatar = ImageOps.fit(src.convert('RGBA'), (176, 176))
            mask = Image.new('L', (176, 176))
            ImageDraw.Draw(mask).ellipse((0, 0, 175, 175), fill=255)
            image.paste(avatar, (110, 245), mask)
        draw.text((330, 275), str(c['name'])[:40], font=font(54), fill='#202125')
        draw.text((330, 345), str(c['handle'])[:45], font=font(40), fill='#666871')
        lines = wrap(c['title'], draw, font(44), 860)
        if len(lines) > 2:
            raise ValueError('A chamada excede duas linhas. Encurte o texto.')
        for i, line in enumerate(lines):
            if draw.textlength(line, font=font(44)) > 860:
                raise ValueError('A chamada contém uma palavra longa demais.')
            draw.text((110, 466 + i * 55), line, font=font(44), fill='#202125')
    # Remove Canva's dashed guide before opening the actual video window.
    if c.get('erase_placeholder'):
        box=c.get('erase_box') or [70,750,940,770]
        if not isinstance(box,list) or len(box)!=4:raise ValueError('Geometria do template inválida.')
        bx,by,bw,bh=[int(v) for v in box]
        if min(bx,by)<0 or min(bw,bh)<1 or bx+bw>1080 or by+bh>1920:raise ValueError('Geometria do template inválida.')
        draw.rectangle((max(0,bx-4),max(0,by-4),min(1080,bx+bw+4),min(1920,by+bh+4)),fill=c['background'])
        draw.rectangle((c['x']-2,c['y']-2,c['x']+c['width']+2,c['y']+c['height']+2),fill=c['background'])
    draw.rounded_rectangle((c['x'], c['y'], c['x'] + c['width'] - 1, c['y'] + c['height'] - 1), radius=max(0,min(200,int(c.get('radius',22)))), fill=(0, 0, 0, 0))
    return image

def command(source, output, artwork, values):
    c = config(values)
    source, output = Path(source).resolve(), Path(output).resolve()
    if source == output:
        raise ValueError('Destino não pode ser o arquivo original.')
    # Bound decoder, filter and encoder workers independently. FFmpeg otherwise
    # scales x264 to all logical CPUs, exceeding the child-process memory cap.
    args = [str(FFMPEG), '-hide_banner', '-nostdin', '-n', '-filter_complex_threads', '2']
    still = source.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp', '.bmp']
    if still:
        args += ['-loop', '1']
    args += INPUT_FLAGS + ['-threads','2','-i',str(source),'-loop','1'] + INPUT_FLAGS + ['-threads','2','-i',str(artwork)]
    mode = 'increase' if c['fit'] == 'cover' else 'decrease'
    w, h = c['width'], c['height']
    fit = f'crop=trunc(iw*{(100-c["crop_left"]-c["crop_right"])/100}/2)*2:trunc(ih*{(100-c["crop_top"]-c["crop_bottom"])/100}/2)*2:trunc(iw*{c["crop_left"]/100}/2)*2:trunc(ih*{c["crop_top"]/100}/2)*2,scale={w}:{h}:force_original_aspect_ratio={mode}'
    fit += f',scale=trunc(iw*{c["zoom"]}/2)*2:trunc(ih*{c["zoom"]}/2)*2'
    fit += f',pad=iw+{2*w}:ih+{2*h}:{w}:{h}:color={c["background"]},crop={w}:{h}:(iw-ow)/2-({c["shift_x"]}*{w}/100):(ih-oh)/2-({c["shift_y"]}*{h}/100)'
    graph = f'[0:v]{fit},setsar=1,pad=1080:1920:{c["x"]}:{c["y"]}:color={c["background"]}[canvas];[canvas][1:v]overlay=0:0:shortest=1:format=auto,format=yuv420p[out]'
    encoder=c.get('_encoder','libx264')
    encoder_options={
        'libx264':['-c:v','libx264','-threads:v','4','-preset','medium','-crf','18'],
        'h264_amf':['-c:v','h264_amf','-quality','quality','-rc','cqp','-qp_i','18','-qp_p','20'],
        'h264_nvenc':['-c:v','h264_nvenc','-preset','p5','-tune','hq','-rc','vbr','-cq','18','-b:v','0'],
        'h264_qsv':['-c:v','h264_qsv','-preset','medium','-global_quality','18'],
    }
    if encoder not in encoder_options: raise ValueError('Encoder inválido.')
    args += ['-filter_complex',graph,'-map','[out]','-map','0:a?'] + encoder_options[encoder] + ['-map_metadata','-1','-map_metadata:s','-1','-map_chapters','-1','-maxrate','20M','-bufsize','40M','-r','30','-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart','-shortest','-shortest_buf_duration','1']
    if still:
        args += ['-t', str(c['seconds'])]
    return args + [str(output)]

def run(source, output, artwork, values, log, process_callback=None, cancel_check=None, on_progress=None):
    chosen=values.get('_encoder','libx264');choices=[chosen]+(['libx264'] if chosen!='libx264' else [])
    cancel_check=cancel_check or (lambda:False)
    output=Path(output)
    partial=output.with_name('.DarkEdit_'+os.urandom(8).hex()+'.partial.mp4')
    try:
        for encoder in choices:
            if cancel_check():raise RuntimeError('Exportação cancelada.')
            partial.unlink(missing_ok=True)
            args=command(source,partial,artwork,{**values,'_encoder':encoder})
            args[-1:-1]=['-progress','pipe:1','-nostats']
            with Path(log).open('a',encoding='utf-8') as stream:stream.write('\nEncoder: '+encoder+'\n')
            result=progress(args,log,on_progress,cancel_check,process_callback)
            if not result and partial.is_file() and partial.stat().st_size>1000:
                if output.exists():raise ValueError('Já existe um vídeo com esse nome. Escolha outro destino.')
                partial.rename(output)
                values['_render_info']={'encoder':encoder,'fallback':encoder!=chosen}
                return output
            if cancel_check():raise RuntimeError('Exportação cancelada.')
        raise RuntimeError('Não foi possível exportar este arquivo. Consulte o diagnóstico do aplicativo.')
    finally:partial.unlink(missing_ok=True)

def detect_scene_crop(source):
    """Suggest scene bounds against uniform black, white or colored borders and sparse captions."""
    boxes=[]
    for timestamp in [0.5,2,5]:
        result=capture([str(FFMPEG),'-hide_banner','-loglevel','error','-ss',str(timestamp)]+INPUT_FLAGS+['-i',str(source),'-frames:v','1','-vf','scale=240:426:force_original_aspect_ratio=decrease','-f','image2pipe','-vcodec','png','-'],timeout=25)
        if not result.stdout: continue
        image=Image.open(io.BytesIO(result.stdout)).convert('RGB');w,h=image.size;pixels=image.load()
        from collections import Counter
        def background_colors():
            colors=[]
            for sample_y in [0,1,min(h-1,4),h-1,max(0,h-4)]:
                counts=Counter(tuple(v//16 for v in pixels[x,sample_y]) for x in range(w))
                color,amount=counts.most_common(1)[0]
                if amount>=w*.7:colors.append(tuple(v*16+8 for v in color))
            return colors
        backgrounds=background_colors()
        def foreground(x,y):
            value=pixels[x,y]
            return not any(max(abs(value[i]-color[i]) for i in range(3))<32 for color in backgrounds)
        rows=[y for y in range(h) if not backgrounds or sum(foreground(x,y) for x in range(w))>=w*.45]
        if not rows or rows[-1]-rows[0]<h*.15: continue
        top,bottom=min(rows),max(rows)+1
        columns=[x for x in range(w) if not backgrounds or sum(foreground(x,y) for y in range(top,bottom))>=(bottom-top)*.45]
        if not columns or columns[-1]-columns[0]<w*.15:continue
        boxes.append((min(columns)/w,top/h,(max(columns)+1)/w,bottom/h))
    if not boxes: raise ValueError('Não foi possível identificar a cena. Ajuste as bordas manualmente.')
    # Union across frames avoids clipping action based on one dark frame.
    left=min(b[0] for b in boxes);top=min(b[1] for b in boxes);right=max(b[2] for b in boxes);bottom=max(b[3] for b in boxes)
    return dict(crop_top=round(top*100,1),crop_bottom=round((1-bottom)*100,1),crop_left=round(left*100,1),crop_right=round((1-right)*100,1))
