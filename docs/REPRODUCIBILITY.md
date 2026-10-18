# 离线运行与源码复现

Release ZIP解压后直接用浏览器打开index.html，前端、25组数据和28组图像已内嵌。Windows限制file://时，可用系统自带PowerShell的Start-Offline.cmd，服务只绑定回环地址，只返回HTML。演示不需要Node、Python、数据库、API Key或云服务。

## 前端重建

仓库包含源码、锁文件、公开数据和图像。安装Node22+及Python后，首次npm ci安装依赖需要联网；已有依赖时，npm run build:final不重新获取数据，输出deliverables/ThawGuard-AI/index.html。根目录index.html保持冻结快照；npm run dev打开dev.html，通过src/observatory-v7/entry.tsx读取开发代码。

## 公开科学计算

安装Python3.11与requirements-observatory-v7.txt需要相应依赖。仓库未捆绑Python本体及各平台wheel，不能声称首次科研环境安装也完全离线。

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-observatory-v7.txt
.venv/Scripts/python.exe scripts/process_v7_public.py
.venv/Scripts/python.exe scripts/experiment_v7.py
.venv/Scripts/python.exe scripts/register_v7_sources.py
.venv/Scripts/python.exe scripts/validate_observatory_v7.py
```

已保留年度SHP及配套文件、Yang/扩展清单ZIP、DSM/WorldCover/SCL原生窗口、OSM/气候JSON、产品目录、像元记录和模型快照。它们不是全部完整卫星场景。已有这些输入和依赖时，重算不需要账户。重新调用acquire下载脚本仍需互联网，接口也可能变化。

重算会改变生成时间；科学结果用独立检查核对，不要求所有带时间戳的文件逐字节不变。使用保存数据重建前端则可核对MANIFEST中的HTML SHA256。

原本机双浏览器和源码重建记录在qa；使用了既有依赖，不是假称全新环境安装。GitHub下载后的解压、回放与导出另见PUBLICATION.md。私有PPT和未发表算法不是运行依赖，也未公开打包。
