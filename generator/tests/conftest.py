# pytest 共享路径：让 tests/ 能 import generator/scripts 下的管线脚本
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # generator/
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT.parent))                   # 仓库根（holo-lab/）
