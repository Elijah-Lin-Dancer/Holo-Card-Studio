"""Create an accurately typeset transparent text layer from project metadata."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from fontTools.ttLib import TTFont
import argparse,json,os

_cmap_cache: dict[str, set[int]] = {}
def _load_cmap(font_path: str) -> set[int]:
    """读字体覆盖表；.ttc 集合需指定 fontNumber=0（PIL 默认 index 0 同理）。"""
    if font_path.lower().endswith(".ttc"):
        return set(TTFont(font_path, fontNumber=0).getBestCmap().keys())
    return set(TTFont(font_path).getBestCmap().keys())

def _glyph_in(font_path: str, ch: str) -> bool:
    """主字体是否含该字符（fontTools cmap 精确判断，PIL 无法区分 tofu）。"""
    if font_path not in _cmap_cache:
        _cmap_cache[font_path] = _load_cmap(font_path)
    return ord(ch) in _cmap_cache[font_path]

def _split_runs(text: str, primary: str, fallback: str) -> list[tuple[str, str]]:
    """按字形覆盖把文本切成连续段（整段渲染保留孟加拉合字 shaping）。"""
    runs: list[tuple[str, str]] = []
    cur_text, cur_font = "", None
    for ch in text:
        font = primary if _glyph_in(primary, ch) else fallback
        if cur_font is None:
            cur_font, cur_text = font, ch
        elif font == cur_font:
            cur_text += ch
        else:
            runs.append((cur_text, cur_font)); cur_text, cur_font = ch, font
    if cur_text:
        runs.append((cur_text, cur_font))
    return runs

def create(project):
    root=Path(project);cfg=json.loads((root/'card-config.json').read_text(encoding='utf-8-sig'))
    with Image.open(root/'assets'/'background.png') as bg:W,H=bg.size
    candidates=[cfg.get('font'),str(Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'/'simkai.ttf'),'/System/Library/Fonts/STHeiti Light.ttc','/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc','/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf']
    font=next((p for p in candidates if p and Path(p).is_file()),None)
    if not font:raise RuntimeError('Provide config.font pointing to an installed font with glyph coverage')
    # 拉丁回退字体：主字体缺拉丁字形（如孟加拉/中文字体）时用
    latin_fb=cfg.get('font_latin') or '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'
    if not Path(latin_fb).is_file():latin_fb='/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'
    # Work on a consistent design canvas, scaling only the generated typography to the source size.
    im=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(im);sx=W/1024;sy=H/1536;gold=(244,208,135,255);cream=(255,241,206,255)
    def txt(x,y,value,size,anchor='la',fill=cream,max_width=850):
        size=max(8,round(size*sx))
        probe=ImageFont.truetype(font,size)
        while d.textbbox((0,0),value,font=probe)[2]>max_width*sx and size>10:size-=1;probe=ImageFont.truetype(font,size)
        stroke_w=max(1,round(sx))
        # 分段：孟加拉等主字体段 + 拉丁回退段，各自整段绘制保留 shaping
        runs=_split_runs(value,font,latin_fb)
        widths=[]
        for seg,fpath in runs:
            f=ImageFont.truetype(fpath,size);bb=d.textbbox((0,0),seg,font=f);widths.append(bb[2]-bb[0])
        total=sum(widths)
        x0,y0=x*sx,y*sy
        start={'ma':x0-total/2,'ra':x0-total}.get(anchor,x0)
        cx=start
        for (seg,fpath),w in zip(runs,widths):
            f=ImageFont.truetype(fpath,size)
            d.text((cx,y0),seg,font=f,fill=fill,anchor='la',stroke_width=stroke_w,stroke_fill=(16,21,27,220))
            cx+=w
    def line(y):d.line((70*sx,y*sy,954*sx,y*sy),fill=gold,width=max(1,round(2*sx)))
    txt(72,49,cfg.get('subtitle',''),25,fill=gold);txt(72,87,cfg.get('title',''),88,max_width=875)
    txt(76,195,cfg.get('collection',''),22,fill=gold);line(245);line(1280)
    txt(512,1300,cfg.get('tagline',''),31,anchor='ma',fill=gold);txt(512,1346,cfg.get('technique',''),69,anchor='ma')
    txt(72,1467,cfg.get('edition','001 / 001'),20,fill=gold);txt(950,1467,'HOLOGRAPHIC',18,anchor='ra',fill=gold,max_width=380)
    dest=root/'assets'/'text.png';im.save(dest);return dest
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('project');a=p.parse_args();print(create(a.project))
