import {meta,type Scenario,type Plan,type Kind} from './types';
import {positionAt,phaseAt} from './simulation';

export function Glyph({kind,size=8}:{kind:Kind;size?:number}){
 const c=meta[kind].color;
 if(kind==='rig')return <path d={`M 0 ${-size} L ${size} ${size} L ${-size} ${size} Z`} fill={c} stroke="#000" strokeWidth="2"/>;
 if(kind==='compressor')return <circle r={size} fill={c} stroke="#000" strokeWidth="2"/>;
 if(kind==='generator')return <path d={`M 0 ${-size} L ${size} 0 L 0 ${size} L ${-size} 0 Z`} fill={c} stroke="#000" strokeWidth="2"/>;
 if(kind==='test')return <path d={`M ${-size} -3 H -3 V ${-size} H 3 V -3 H ${size} V 3 H 3 V ${size} H -3 V 3 H ${-size} Z`} fill={c} stroke="#000" strokeWidth="1"/>;
 return <rect x={-size} y={-size*.6} width={size*2} height={size*1.2} rx={kind==='water'?2:0} fill={c} stroke="#000" strokeWidth="2"/>;
}

export default function Map({scenario:s,plan,time,selected,onSelect,ranges,routes}:{scenario:Scenario;plan:Plan|null;time:number;selected:string;onSelect:(id:string)=>void;ranges:boolean;routes:boolean}){
 const scale=Math.max(s.width,s.height)/1000;
 const pad=40*scale;
 const tracks=plan?.machines??s.machines.map(m=>({...m,used:false,events:[],travel_hours:0,service_hours:0}));
 const points=tracks.map(t=>({t,p:positionAt(t,time)}));
 return <svg className="field" viewBox={`${-pad} ${-pad} ${s.width+pad*2} ${s.height+pad*2}`} role="img" aria-label="Mapa de pozos y equipos con coordenadas en metros">
   <defs><pattern id="dots" width={50*scale} height={50*scale} patternUnits="userSpaceOnUse"><circle r={.7*scale} fill="#242424"/></pattern></defs>
   <rect width={s.width} height={s.height} fill="url(#dots)" stroke="#333" strokeWidth={scale}/>
   {[0,.25,.5,.75,1].map(f=><g key={f} className="axis" fontSize={10*scale}><text x={s.width*f} y={s.height+22*scale} textAnchor="middle">{Math.round(s.width*f)}</text><text x={-12*scale} y={s.height*(1-f)+4*scale} textAnchor="end">{Math.round(s.height*f)}</text></g>)}
   <text className="axis" x={s.width} y={s.height+36*scale} textAnchor="end" fontSize={9*scale}>X / m</text>
   <text className="axis" x={-12*scale} y={-16*scale} fontSize={9*scale}>Y / m</text>
   {plan&&tracks.filter(t=>routes||selected===t.id).map(t=><g key={'route'+t.id}>{t.events.filter(e=>e.state==='travel').map((e,i)=><polyline key={i} points={e.path.map(p=>`${p.x},${s.height-p.y}`).join(' ')} fill="none" stroke={meta[t.kind].color} strokeOpacity={selected===t.id ? .55 : .2} strokeWidth={scale*1.2} strokeDasharray={`${4*scale} ${5*scale}`}/>)}</g>)}
   {ranges&&points.map(({t,p})=>{
    const ev=t.events.find(e=>e.start<=time&&time<e.end);
    if(!t.radius||!ev||!['service','setup','reserved'].includes(ev.state))return null;
    return <g key={'range'+t.id}><circle cx={p.x} cy={s.height-p.y} r={t.radius} fill={meta[t.kind].color} fillOpacity={.035} stroke={meta[t.kind].color} strokeOpacity={.4} strokeDasharray={`${5*scale} ${5*scale}`} strokeWidth={scale}/>{ev.wells.map(wid=>{const w=s.wells.find(w=>w.id===wid)!;return <line key={wid} x1={p.x} y1={s.height-p.y} x2={w.x} y2={s.height-w.y} stroke={meta[t.kind].color} strokeOpacity={.5} strokeWidth={scale}/>;})}</g>;
   })}
   <g transform={`translate(${s.depot.x},${s.height-s.depot.y})`}><rect x={-12*scale} y={-12*scale} width={24*scale} height={24*scale} fill="#000" stroke="#666" strokeWidth={scale}/><text y={28*scale} fill="#777" fontSize={10*scale} textAnchor="middle">BASE</text></g>
   {s.wells.map(w=>{
    const wp=plan?.wells.find(p=>p.id===w.id);const state=wp?phaseAt(wp,time):{color:'#555',progress:0,label:'Pendiente',id:'waiting'};
    const r=12*scale;
    return <g key={w.id} transform={`translate(${w.x},${s.height-w.y})`} className="map-item" role="button" tabIndex={0} aria-label={`Pozo ${w.id}: ${state.label}`} onClick={()=>onSelect(w.id)} onKeyDown={e=>{if(e.key==='Enter'||e.key===' ')onSelect(w.id);}}>
      <title>{w.id} · ({w.x.toFixed(1)}, {w.y.toFixed(1)}) · {state.label}</title>
      {selected===w.id&&<circle r={21*scale} fill="none" stroke="#fff" strokeWidth={scale} strokeDasharray={`${2*scale} ${4*scale}`}/>}
      <circle r={r} fill="#000" stroke="#333" strokeWidth={3*scale}/>
      <circle r={r} fill="none" stroke={state.color} strokeWidth={3*scale} strokeDasharray={`${Math.max(.02,state.progress)*2*Math.PI*r} ${2*Math.PI*r}`} transform="rotate(-90)"/>
      <circle r={4*scale} fill={state.color}/>
      <text y={-22*scale} fontSize={11*scale} fill={selected===w.id?'#fff':'#aaa'} textAnchor="middle">{w.id}</text>
      {state.id!=='waiting'&&<text y={29*scale} fontSize={9*scale} fill={state.color} textAnchor="middle">{state.label}</text>}
    </g>;
   })}
   {points.map(({t,p},i)=>{
    const overlapping=points.filter(q=>Math.hypot(q.p.x-p.x,q.p.y-p.y)<4*scale);
    const index=overlapping.findIndex(q=>q.t.id===t.id);
    const angle=index*Math.PI*2/Math.max(1,overlapping.length);
    const offset=overlapping.length>1?18*scale:0;
    const dx=Math.cos(angle)*offset,dy=Math.sin(angle)*offset;
    const ev=t.events.find(e=>e.start<=time&&time<e.end);
    return <g key={t.id} className="map-item" role="button" tabIndex={0} aria-label={`Máquina ${t.id}`} onClick={()=>onSelect(t.id)} onKeyDown={e=>{if(e.key==='Enter'||e.key===' ')onSelect(t.id);}}>
      <title>{t.id} · {meta[t.kind].short} · ({p.x.toFixed(1)}, {p.y.toFixed(1)}) · {ev?.label??'Disponible'}</title>
      {offset>0&&<line x1={p.x} y1={s.height-p.y} x2={p.x+dx} y2={s.height-p.y+dy} stroke={meta[t.kind].color} strokeWidth={scale} strokeOpacity={.5}/>}
      <g transform={`translate(${p.x+dx},${s.height-p.y+dy}) scale(${scale})`} opacity={plan&&!t.used ? .35 : 1}>
        {selected===t.id&&<circle r={15} stroke="#fff" fill="none" strokeWidth={1}/>}
        <Glyph kind={t.kind}/><text x={12} y={-8-(i%2)*2} fill={meta[t.kind].color} fontSize="9" paintOrder="stroke" stroke="#000" strokeWidth="3">{t.id}</text>
      </g>
    </g>;
   })}
 </svg>;
}
