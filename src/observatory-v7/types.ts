export type Observation={date:string;ordinal:number;item:string;platform:string;values:number[];dn:number[];qa_pixel:number;qa_radsat:number;quality:string;cfmask:number;ndvi:number|null;source_url:string;used_in_model:boolean};
export type Segment={start:string;break:string|null;n:number;coefs:number[][];rmse:number[]};
export type Snapshot={as_of:string;n:number;mode:number;segments:Segment[];current:null|{start:string;coefs:number[][];consecutive_anomalies:number}};
export type PointRecord={key:string;inventory_id:number|null;coordinates:[number,number];name:string;role:string;selection:string;bounds:[number,number,number,number];observations:Observation[];valid_count:number;quality_counts:Record<string,number>;replays:Snapshot[];first_seen_breaks:{estimated_change:string;first_detectable_observation:string;calendar_days:number}[];errors:unknown[]};
export type ImageRecord={key:string;year:number;date:string;item:string;bounds:[number,number,number,number];path:string;source_url:string;cloud_cover_scene_pct:number;rendering:string;sensor?:string;resolution_m?:number;purpose?:string};
export type Site={id:number;coordinates:[number,number];timeseries:{year:number;area_ha:number|null;polygon_count:number}[];area_2022_ha:number;delta_ha:number};
export type Data={meta:Record<string,any>;points:PointRecord[];images:ImageRecord[];summary:Record<string,any>;sites:Site[];terrain:Record<string,any>;layers:Record<number,any>;content:Record<string,any>;corroboration:any;corroborationGeo:any;context:any;infrastructure:any;assistance:any;sentinelQuality:any};
declare global {interface Window{__TG_IMAGES?:Record<string,string>}}
export const asset=(s:string)=>window.__TG_IMAGES?.[s]||s;
export const sourceInventory='https://zenodo.org/records/10928346';
export const qualityNames:Record<string,string>={clear:'有效陆地',water:'水体标记',cloud:'云／卷云',shadow:'云影',snow:'积雪',saturated:'饱和／遮蔽',nodata:'无数据',range:'反射率越界'};
export const dateOrdinal=(s:string)=>Math.round(Date.parse(s+'T00:00:00Z')/86400000)+719163;
export const at=(p:PointRecord,d:string)=>p.replays.filter(s=>s.as_of<=d).at(-1)||null;
export const valid=(o:Observation)=>o.used_in_model;
export function download(name:string,content:string,mime='application/json'){const u=URL.createObjectURL(new Blob([content],{type:mime})),a=document.createElement('a');a.href=u;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(u),1000)}
