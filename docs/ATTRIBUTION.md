# 科研、数据与软件署名

本文件对不同来源分别署名，不将第三方数据许可扩展为整个应用的许可证。原始数据及论文权利归相应权利人；公开接口服务商不是所有数据的作者。核对日期 2026-10-18。

## 科研方法与团队材料

- Zhu, Z., & Woodcock, C. E. (2014). *Continuous change detection and classification of land cover using all available Landsat data*. Remote Sensing of Environment, 144, 152–171. [原论文](https://doi.org/10.1016/j.rse.2014.01.011)。是 CCDC 方法基础；本 Demo 没有实现其完整分类链。
- Ye, S., Rogan, J., Zhu, Z., & Eastman, J. R. (2021). *A near-real-time approach for monitoring forest disturbance using Landsat time series: Stochastic continuous change detection*. Remote Sensing of Environment, 252, 112167. [原论文](https://doi.org/10.1016/j.rse.2020.112167)。本案例复现不把原森林应用性能移植为 RTS 精度。
- Su Ye / [pyxccd](https://github.com/Remote-Sensing-of-Land-Resource-Lab/pyxccd)，实际使用 1.1.0 公开默认配置；仓库标示 Apache-2.0。Python 库不嵌入浏览器，仅使用预计算结果。算法贡献归原作者。
- 4 月《21世纪青藏高原热融滑塌空间格局演变分析》与 5 月《基于多源遥感数据的青藏高原热融滑塌近实时探测及损害评估》为用户提供的科研材料。材料署名为李灿、朱书悦、许哲荣，指导教师叶粟；这不是本 Demo 全部代码作者或正式参赛名单的认定。原 PPT 和未发表方法参数未分发。指导/合作关系不自动构成团队对公开通用算法的独占权利或机构背书。

## 公开数据与图像

|来源|署名、许可与处理|
|---|---|
|年度 RTS 清单|Xia、Liu、Mu、Peng、Zhao、Huang、Luo、Fan；[Zenodo 10928346](https://zenodo.org/records/10928346)，CC BY 4.0。提取研究窗、保留完整相交边界、计算面积与差集；不是团队新识别清单。|
|北麓河 RTS 清单|Yang、Qiu、Ye、Liu、Zhang、Zhu；[Zenodo 8103939](https://zenodo.org/records/8103939)，CC BY 4.0。核对标签与空间重叠，不将活动状态改为滑塌/非滑塌真值。|
|扩展历史清单|Xia、Zhao、Liu、Huang、Gascoin、Lara；[Zenodo 21693485](https://zenodo.org/records/21693485)，CC BY 4.0。原记录标题为 1964—2024；不与原年度清单拼为同一面积时序。|
|Landsat|Landsat data courtesy of the U.S. Geological Survey。[USGS C2 L2](https://www.usgs.gov/landsat-missions/landsat-collection-2-level-2-science-products)，公开数据经 Microsoft Planetary Computer 读取。保留产品编号、DN、QA、反射率换算与像元时序，生成局部 RGB。|
|Sentinel-2|Contains modified Copernicus Sentinel data [2019–2021]。[Copernicus 数据条款](https://www.copernicus.eu/en/access-data/copyright-and-licences)，[获取接口](https://planetarycomputer.microsoft.com/dataset/sentinel-2-l2a)。裁剪、统一拉伸、SCL 掩膜和重投影；仅作形态参考。|
|Copernicus DEM|Copernicus GLO-30 DSM，[AWS 来源及许可入口](https://registry.opendata.aws/copernicus-dem/)。© DLR e.V. 2010–2014；© Airbus Defence and Space GmbH 2014–2018；由 EU/ESA 的 COPERNICUS 提供。原生窗口经重投影派生地形统计，不是未处理原瓦片或现场 DTM。|
|ESA WorldCover|Zanaga et al.，WorldCover 2020 v100 / 2021 v200，[2020 DOI](https://doi.org/10.5281/zenodo.5571936)、[2021 DOI](https://doi.org/10.5281/zenodo.7254221)，CC BY 4.0。© ESA WorldCover project [2020/2021] / Contains modified Copernicus Sentinel data ([2020/2021]) processed by ESA WorldCover consortium。对固定多边形内类别做统计；年份对应实际产品年份。|
|OSM|© OpenStreetMap contributors，[ODbL-1.0](https://opendatacommons.org/licenses/odbl/1-0/)，[署名说明](https://www.openstreetmap.org/copyright)。Overpass 2026-10-18 快照；派生设施矢量与测距见 `osm-derived.geojson`，该 OSM 数据部分仍按 ODbL 提供。|
|气候再分析|Copernicus Climate Change Service / ECMWF 的 ERA5、ERA5-Land，经 [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api) 获取；API 数据署名 CC BY 4.0。原生格点逐日数据分别聚合为月值，不能称作地面测站。|
|静态底图|NASA GIBS Blue Marble Shaded Relief，credit NASA；[NASA 图像使用说明](https://www.nasa.gov/nasa-brand-center/images-and-media/)。静态地理背景，不是所选年份影像或滑塌形态证据；没有使用 NASA 标志或暗示背书。|
|旧地形比较|Mapzen / AWS Terrain Tiles，[来源](https://registry.opendata.aws/terrain-tiles/)、[各底层数据署名要求](https://github.com/tilezen/joerd/blob/master/docs/attribution.md)。仅保留既有静态派生摘要；底层 DEM 和垂直基准未逐瓦片确认，不能标为 Copernicus 或实测。该区域全球底层数据提供者包括 USGS（SRTM / GMTED2010）及 NOAA（ETOPO1）；未声称已经确定每格来源，不分发新的 Mapzen 原瓦片。|

CC BY 4.0 许可入口为 [Creative Commons](https://creativecommons.org/licenses/by/4.0/)。完整文件路径和哈希见 `source_registry.csv`；这些来源的署名与免责不表示数据作者认可本项目的结论。

## 前端软件

React、React DOM、Scheduler 使用 MIT；Leaflet 使用 BSD-2-Clause；Lucide 使用 ISC（含其保留的 Feather 贡献声明）。安装版本见 `SOFTWARE_VERSIONS.json`，完整版权许可文本见 `THIRD_PARTY_NOTICES.txt`。完整文本也已嵌入 `index.html` 的 `tg-third-party-notices` 文本块，单独转发 HTML 时仍予保留。

本轮没有复制其他参赛项目的模型结果、代码或指标作为本项目成果。其他网站仅提供交互参考。
