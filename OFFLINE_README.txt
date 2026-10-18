ThawGuard AI V7 离线使用

1. 将 Release ZIP 完整解压到本机文件夹。不要在压缩包内直接打开。
2. 双击 index.html，使用 Edge 或 Chrome。核心地图、影像、数据与交互均无需网络，不需要安装 npm、Python 或第三方插件。
3. 如果单位浏览器禁止 file://，双击 Start-Offline.cmd。它使用 Windows 自带 PowerShell，仅在 127.0.0.1:8017 提供当前 HTML，自动打开浏览器；保留服务窗口，关闭窗口或 Ctrl+C 停止。
4. 如果 8017 端口已占用，在本目录终端运行：
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Start-Offline.ps1 -Port 0 -OpenBrowser
   Port 0 自动选择本机空闲端口。

三分钟路线
首页 → 查看RTS 1938真实监测案例 → 回到首次检出前 / 加入首次检出观测 → 核对影像和光谱 → 地表与影响 → 导出当前判读说明。

注意
人工意见仅保存在当前浏览器本机，协作请导出报告或 JSON。外部论文、原始产品和数据源链接需要联网，但不会影响内嵌演示。这里是历史遥感科研核查原型，不提供灾前预测或正式预警。源码复算所需的 Node / Python 依赖并未捆绑为跨平台运行环境；日常演示无需这些依赖。
