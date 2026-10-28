export type Kind='rig'|'compressor'|'generator'|'fluid'|'test'|'water';
export type Point={x:number;y:number};
export type Well=Point&{id:string;durations:Record<string,number>;water_demand:number|null};
export type Machine={id:string;kind:Kind;initial:Point;speed:number;radius:number;simultaneous:number;capacity:number;setup:number;disconnect:number;available:number};
export type Requirement={kind:Exclude<Kind,'rig'|'water'>;phases:string[];demand:number};
export type Scenario={name:string;width:number;height:number;seed:number;depot:Point;wells:Well[];machines:Machine[];durations:Record<string,number>;requirements:Requirement[];water_demand:number;tank_capacity:number;delivery_time:number;refill_time:number;metric:'euclidean_demo'|'manhattan_demo';mode:'schedule'|'fleet';deadline:number;time_limit:number;candidates_per_well:number};
export type Phase={id:string;label:string;start:number;end:number;machines:string[]};
export type WellPlan=Point&{id:string;phases:Phase[];completion:number;water_demand:number};
export type Motion={state:string;start:number;end:number;from:Point;to:Point;path:Point[];wells:string[];label:string};
export type Track={id:string;kind:Kind;used:boolean;initial:Point;radius:number;capacity:number;simultaneous:number;events:Motion[];travel_hours:number;service_hours:number};
export type Booking={machine:string;well:string;first:number;last:number;position:Point;start:number;end:number;work_start:number;work_end:number;demand:number;water:boolean};
export type Plan={status:string;makespan:number;construction_end:number;solve_seconds:number;solutions:number;relative_gap:number;objective_value:number;objective_bound:number;proof_scope:string;objective:string;candidate_count:number;model_variables:number;assumptions:string[];wells:WellPlan[];machines:Track[];bookings:Booking[];fleet_used:Record<Kind,number>;fleet_available:Record<Kind,number>;scenario:Scenario;verification:{valid:boolean;checks:string[]};cancelled:boolean};
export type Progress={stage:string;message:string;solutions?:number;best_hours?:number;elapsed?:number};
export const kinds:Kind[]=['rig','compressor','generator','fluid','test','water'];
export const meta:Record<Kind,{label:string;short:string;color:string;prefix:string;unit:string}>={
 rig:{label:'Perforadoras',short:'Perforadora',color:'#d0eb8c',prefix:'D',unit:'unidad'},
 compressor:{label:'Compresores',short:'Compresor',color:'#ffb86b',prefix:'C',unit:'m³/min'},
 generator:{label:'Generadores',short:'Generador',color:'#c1a0ff',prefix:'G',unit:'kW'},
 fluid:{label:'Circuitos agua / lodo',short:'Circulación',color:'#f78bb2',prefix:'L',unit:'m³/h'},
 test:{label:'Equipos de ensayo',short:'Ensayo',color:'#6dd8d2',prefix:'E',unit:'pozos'},
 water:{label:'Camiones de agua',short:'Agua',color:'#77acff',prefix:'A',unit:'m³'},
};
export const phases=[['prepare','Preparación','#777777'],['drill','Perforación','#d0eb8c'],['condition','Acondicionamiento','#ffb86b'],['test_setup','Montaje ensayo','#b0b0b0'],['pump','Bombeo de prueba','#6dd8d2'],['recovery','Recuperación','#c1a0ff'],['test_remove','Desmontaje ensayo','#939aab']];
