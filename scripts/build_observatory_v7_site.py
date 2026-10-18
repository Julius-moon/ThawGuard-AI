from pathlib import Path
import shutil
R=Path(__file__).resolve().parents[1];d=R/'dist-observatory';d.mkdir(exist_ok=True)
# The default production page is fully self-contained. No legacy public/model
# folder is copied into this release. Existing legacy assets remain historical.
shutil.copyfile(R/'deliverables/observatory-v7/ThawGuard_连续观测与事件证据_v7.html',d/'index.html')
print('Clean production output: dist-observatory/index.html (no legacy models/assets)')
