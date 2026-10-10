"""Build a user-owned Blender/Three.js project from prepared layered artwork."""
from pathlib import Path
import argparse,json,shutil,subprocess,sys,os
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ensure_blender import ensure_blender
from validate_assets import validate
from generate_typography import create
from qa.quality_gate import run_gate as run_qa

def main():
    p=argparse.ArgumentParser();p.add_argument('--project',required=True);p.add_argument('--blender');p.add_argument('--skip-render',action='store_true');p.add_argument('--skip-npm',action='store_true');p.add_argument('--skip-qa',action='store_true',help='跳过 AI 素材质检门禁（调试用）');p.add_argument('--force',action='store_true',help='质检不过仍继续（手动放行）');p.add_argument('--render-mode',default=None,choices=['standard','premium'],help='渲染工艺线：standard=美术近似镭射（默认，随 config.render_mode 或默认）/ premium=物理仿真全息（需 config.foil 参数块）');p.add_argument('--smoke',action='store_true',help='快速冒烟渲染：低采样/小分辨率/少帧，验证链路不崩');a=p.parse_args()
    root=Path(a.project).resolve();scripts=Path(__file__).resolve().parent;web_template=scripts/'web-template-holographic'
    config=root/'card-config.json'
    if not config.exists():raise FileNotFoundError('Write card-config.json from references/config.example.json first')
    if not (root/'assets'/'text.png').exists():create(root)
    validate(root)
    # —— AI 素材质检门禁（B-2）：素材不过关 → 中断提示重生成（--force 放行 / --skip-qa 跳过）
    if not a.skip_qa:
        cfg0 = json.loads(config.read_text(encoding='utf-8-sig'))
        series = cfg0.get('qa_series', 'default')
        overrides = cfg0.get('qa_overrides', [])
        qa = run_qa(root, series)
        qa['issues'] = [i for i in qa['issues'] if not any(ov in i for ov in overrides)]
        if qa['issues'] and not a.force:
            print('✗ QA 门禁未通过 —— 素材需重生成:', file=sys.stderr)
            for i in qa['issues']: print('   -', i, file=sys.stderr)
            print('  (QA 报告: qa_reports/%s.json ｜ 确认可放行: --force ｜ 跳过: --skip-qa)' % root.name, file=sys.stderr)
            raise SystemExit(1)
        (root/'qa_reports').mkdir(exist_ok=True)
        (root/'qa_reports'/f'{root.name}.json').write_text(json.dumps(qa, ensure_ascii=False, indent=2), encoding='utf8')
    blender=ensure_blender(root,a.blender)
    env=os.environ.copy();prefs=root/'tools'/'blender-config';prefs.mkdir(parents=True,exist_ok=True);env['BLENDER_USER_CONFIG']=str(prefs)
    cmd=[str(blender),'--background','--factory-startup','--python-exit-code','1','--python',str(scripts/'build_card.py'),'--',str(root)]
    if a.render_mode: cmd += ['--render-mode', a.render_mode]
    if a.skip_render:cmd.append('--skip-render')
    if a.smoke:cmd.append('--smoke')
    subprocess.run(cmd,check=True,env=env)
    if not (root/'card.blend').exists():raise RuntimeError('Blender did not save card.blend; inspect its log')
    subprocess.run([str(blender),'--background','--factory-startup','--python-exit-code','1','--python',str(scripts/'export_web.py'),'--',str(root)],check=True,env=env)
    if not (root/'web'/'assets'/'card.glb').exists():raise RuntimeError('GLB export failed')
    web=root/'web';shutil.copytree(web_template,web,dirs_exist_ok=True)
    cfg=json.loads(config.read_text(encoding='utf-8-sig'));cfg['assets']={name:'./assets/'+name+'.png' for name in ['subject','background','text','lineart']};cfg['assets']['model']='./assets/card.glb'
    (web/'card-config.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf8')
    for name in ['subject.png','background.png','text.png','lineart.png']:shutil.copy2(root/'assets'/name,web/'assets'/name)
    if not a.skip_npm:
        npm=shutil.which('npm.cmd') or shutil.which('npm')
        if not npm:raise RuntimeError('Install Node.js/npm, then run npm install --ignore-scripts in web/')
        subprocess.run([npm,'install','--ignore-scripts','--no-audit','--no-fund'],cwd=web,check=True)
    print('Completed:',root/'card.blend');print('Preview: node',web/'server.mjs');print('Open http://127.0.0.1:4173 after starting the server')
if __name__=='__main__':main()
