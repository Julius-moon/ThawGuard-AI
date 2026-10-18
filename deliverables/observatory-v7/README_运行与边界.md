# ThawGuard V7 · 公开数据与科学判读专项升级

双击同目录 `ThawGuard_连续观测与事件证据_v7.html`。无需联网、登录或安装软件。给协作者直接发送这一份HTML，或发送协作展示ZIP。人工记录保存在当前浏览器本机，报告/JSON可以交接，不会自动跨设备同步。

当前源码接续V6，保留原六页面和五阶段科研流程。V5/V6原件未改，未退回派单/回执系统。本轮不制作或重命名旧PPT为V7。

## 三分钟操作

首页点击“查看RTS 1938真实监测案例” → 比较2019/2021或2020-09-21/10-01真实影像 → 回放首次检出前/后 → 查看可解释核查 → 打开“地表与影响”看覆盖和设施 → 案例顶部导出当前判读说明。详细步骤见 `THREE_MINUTE_GUIDE.md`。

应理解的结论是：公开S-CCD在一个固定30m像元检出持续光谱变化；历史清单与影像支持已有滑塌位置，但没有独立验证断点所对应的具体地表过程或整片滑塌首次发生时间。10m Sentinel为形态参照，不是10m S-CCD输入。56天是回放两个观测日期的间隔，不是提前预警。

## 本轮实际计算

- Copernicus GLO-30 DSM海拔/坡度中位数4828.49m/4.818°、坡度P90、坡向圆均值与集中度、250m缓冲起伏，与Mapzen交叉核对。原生1角秒、EGM2008，采用AWS保留版本而非GEE2024_1新版。
- 原生SCL质量验证与实际掩膜；2019/2021及2020断点前后共四景统一RGB渲染。原来2020-08-19参照仍保留。
- 原年度清单属性面积与投影几何面积分别核算，2016—2022净属性面积变化15.46ha，几何新增15.51ha、退出0.06ha，口径分别标注。
- 2020/2021 WorldCover固定范围类别比例、同传感器夏季光谱统计。真实NDVI没有单调下降，不包装成植被损失。
- 当前OSM快照与版本、路径/道路、铁路、水系片段及最短距离。最近记录路径约9.77km、G109约24.07km、铁路约24.23km；不是工程风险等级或运移路径。
- ERA5-Land原生格点温度与ERA5降水分别获取，1096天/变量，聚合完整36个月；不把ERA5-Land缺失降水补零，也不冒充直接GEE月度资产。
- 原公开S-CCD12次独立前缀重跑、NDVI因果滚动基线和首检时多波段残差。459条公开清单审查得知0个核实非RTS标签，N是不活跃RTS。因此不训练伪二分类器，明确采用可审计规则辅助，模型卡给出最小补样与验证协议。

## 文件

`AUDIT.md` 保存改动前审计和猫咪来源边界；`DATA_AUDIT.md` 保存数据/投影/时间口径；`source_registry.csv` 保存16条来源与文件哈希；`MODEL_CARD.md`、`MODEL_RUN.json`、`model_run.log` 保存实际方法与停止训练的依据；`COPY_REVIEW.md` 保存文案和既有PPT一致性检查；`screenshots/` 均为实际浏览器截图，不是概念生图。

最终验证：78项离线浏览器回归、116项数据/方法完整性检查，以及实际HTTP预览路线。软件和数据一致性通过，不等于现场测量精度、RTS分类精度或管理收益已验证。三分钟路线尚未经过真实评委理解度测试。

此轮没有收到附件引用的两张反馈原图。干净、无扩展Edge截图未复现猫咪，源组件也未发现相应素材；没有据此断言外部软件来源或修改系统宠物。功能提示已改为正常文档流，避免覆盖科研画面。

## 源码复现

Node22+：`npm ci` → `npm run build` → `npm run preview:observatory`，本机端口4197。源码 `src/observatory-v7`，完整离线输出在本目录；生产入口 `dist-observatory/index.html`。

Python3.11：创建`.venv`，安装`requirements-observatory-v7.txt`。公开输入脚本为 `acquire_v7_public.py`、`acquire_v7_sentinel.py`、`acquire_v7_climate.py`；处理与实验依次为 `process_v7_public.py`、`experiment_v7.py`、`register_v7_sources.py`。输入已随完整源码/公开数据包保存，重算无需账户。`npm run test:science`重跑完整性检查，`npm run test:observatory`使用本机Edge验证离线交互。

本网页读取Python预计算结果，不宣称浏览器实时获取卫星数据。没有侵蚀深度、冰含量及地面碳过程约束，不输出体积、碳排、损失金额或设施失效概率；这些进入可展开的研究说明。团队未发表阈值、参数、私有样本和科研原图不在交付包中。

公开数据许可与署名见来源表。Copernicus DEM：© DLR e.V. 2010–2014；© Airbus Defence and Space GmbH 2014–2018，由EU/ESA的COPERNICUS提供；WorldCover和Zenodo清单为CC-BY-4.0，OSM为ODbL。Contains modified Copernicus Sentinel data [2019–2021]。旧来源的保留时间以原任务日志/文件mtime近似，不冒充传感器采集时刻。
