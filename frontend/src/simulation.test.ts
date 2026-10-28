import {describe,it,expect} from 'vitest';
import {positionAt,phaseAt,inventoryAt} from './simulation';
import type {Track,WellPlan,Plan} from './types';
const track:Track={id:'A01',kind:'water',used:true,initial:{x:0,y:0},radius:0,simultaneous:1,capacity:20,travel_hours:2,service_hours:1,events:[
 {state:'travel',start:0,end:2,from:{x:0,y:0},to:{x:10,y:10},path:[{x:0,y:0},{x:10,y:0},{x:10,y:10}],wells:[],label:'Viaje'},
 {state:'delivery',start:2,end:3,from:{x:10,y:10},to:{x:10,y:10},path:[{x:10,y:10},{x:10,y:10}],wells:['P01'],label:'Entrega'}]};
describe('Coordenadas de la simulación',()=>{
 it('interpola sobre el recorrido ortogonal, no sobre una diagonal',()=>{expect(positionAt(track,.5)).toEqual({x:5,y:0});expect(positionAt(track,1.5)).toEqual({x:10,y:5});});
 it('mantiene posición durante entrega y después de terminar',()=>{expect(positionAt(track,2.5)).toEqual({x:10,y:10});expect(positionAt(track,10)).toEqual({x:10,y:10});});
 it('respeta los extremos del recorrido',()=>{expect(positionAt(track,0)).toEqual({x:0,y:0});expect(positionAt(track,2)).toEqual({x:10,y:10});});
});
const well:WellPlan={id:'P01',x:10,y:10,completion:8,water_demand:12,phases:[{id:'prepare',label:'Preparación',start:1,end:3,machines:[]},{id:'drill',label:'Perforación',start:3,end:7,machines:[]},{id:'condition',label:'Acondicionamiento',start:7,end:8,machines:[]}]};
it('identifica fase y finalización',()=>{expect(phaseAt(well,0).id).toBe('waiting');expect(phaseAt(well,5).progress).toBe(.5);expect(phaseAt(well,8).id).toBe('done');});
it('consume agua solo después de entrega y durante perforación',()=>{const plan={bookings:[{water:true,well:'P01',end:3}]} as Plan;expect(inventoryAt(plan,well,2)).toBe(0);expect(inventoryAt(plan,well,3)).toBe(12);expect(inventoryAt(plan,well,5)).toBe(6);expect(inventoryAt(plan,well,9)).toBe(0);});
