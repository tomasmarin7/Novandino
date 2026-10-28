import type {Point,Track,WellPlan,Plan} from './types';

export function positionAt(track:Track,time:number):Point {
 const event=track.events.find(e=>e.start<=time&&time<e.end);
 if(!event){const past=track.events.filter(e=>e.end<=time);return past.at(-1)?.to??track.initial;}
 if(event.state!=='travel')return event.from;
 const lengths=event.path.slice(1).map((p,i)=>Math.hypot(p.x-event.path[i].x,p.y-event.path[i].y));
 const total=lengths.reduce((a,b)=>a+b,0);
 let remaining=total*Math.max(0,Math.min(1,(time-event.start)/(event.end-event.start)));
 for(let i=0;i<lengths.length;i++){
   if(remaining<=lengths[i]&&lengths[i]>0){const f=remaining/lengths[i];return {x:event.path[i].x+(event.path[i+1].x-event.path[i].x)*f,y:event.path[i].y+(event.path[i+1].y-event.path[i].y)*f};}
   remaining-=lengths[i];
 }
 return event.to;
}
export function phaseAt(w:WellPlan,time:number){
 if(time>=w.completion)return {label:'Terminado',color:'#d0eb8c',progress:1,id:'done'};
 const p=w.phases.find(p=>p.start<=time&&time<p.end);
 if(!p)return {label:time<w.phases[0].start?'Pendiente':'Espera de equipo',color:'#666666',progress:0,id:'waiting'};
 return {label:p.label,color:['#777','#d0eb8c','#ffb86b','#b0b0b0','#6dd8d2','#c1a0ff','#939aab'][w.phases.indexOf(p)],progress:(time-p.start)/(p.end-p.start),id:p.id};
}
export function inventoryAt(plan:Plan,well:WellPlan,time:number){
 const delivery=plan.bookings.find(b=>b.water&&b.well===well.id);
 if(!delivery||time<delivery.end)return 0;
 const p=well.phases.find(p=>p.id==='drill')!;
 return well.water_demand*(1-Math.max(0,Math.min(1,(time-p.start)/(p.end-p.start))));
}
export function hours(v:number){return `${v.toLocaleString('es-CL',{maximumFractionDigits:1})} h`;}
export function timeLabel(v:number){const d=Math.floor(v/24);return `D${d+1} · ${String(Math.floor(v%24)).padStart(2,'0')}:${String(Math.floor((v%1)*60+1e-5)).padStart(2,'0')}`;}
