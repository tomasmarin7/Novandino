"""Explicit, editable scenario contract. All coordinates are synthetic local metres."""
from __future__ import annotations

import math
import random
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

KINDS = ('rig', 'compressor', 'generator', 'fluid', 'test', 'water')
PHASES = ('prepare', 'drill', 'condition', 'test_setup', 'pump', 'recovery', 'test_remove')
LABELS = ('Preparación', 'Perforación', 'Acondicionamiento', 'Montaje ensayo', 'Bombeo de prueba', 'Recuperación', 'Desmontaje ensayo')

class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)

class Point(Strict):
    x: float = Field(ge=0, le=100000)
    y: float = Field(ge=0, le=100000)

class Well(Point):
    id: str = Field(min_length=1, max_length=40)
    durations: dict[str, float] = Field(default_factory=dict)
    water_demand: float | None = Field(default=None, ge=0, le=10000)

class Machine(Strict):
    id: str = Field(min_length=1, max_length=40)
    kind: Literal['rig', 'compressor', 'generator', 'fluid', 'test', 'water']
    initial: Point
    speed: float = Field(default=400, ge=1, le=10000)
    radius: float = Field(default=250, ge=0, le=100000)
    simultaneous: int = Field(default=1, ge=1, le=20)
    capacity: float = Field(default=100, gt=0, le=10000)
    setup: float = Field(default=0.5, ge=0, le=100)
    disconnect: float = Field(default=0.25, ge=0, le=100)
    available: float = Field(default=0, ge=0, le=10000)

class Requirement(Strict):
    kind: Literal['compressor', 'generator', 'fluid', 'test']
    phases: list[str]
    demand: float = Field(default=1, gt=0, le=10000)

class Scenario(Strict):
    name: str = Field(default='Campaña de demostración', max_length=100)
    width: float = Field(default=1000, ge=10, le=100000)
    height: float = Field(default=700, ge=10, le=100000)
    seed: int = Field(default=42, ge=0, le=2147483647)
    depot: Point = Field(default_factory=lambda: Point(x=50, y=50))
    wells: list[Well] = Field(min_length=1, max_length=16)
    machines: list[Machine] = Field(min_length=1, max_length=40)
    durations: dict[str, float]
    requirements: list[Requirement]
    water_demand: float = Field(default=12, ge=0, le=10000)
    tank_capacity: float = Field(default=20, gt=0, le=10000)
    delivery_time: float = Field(default=0.5, gt=0, le=100)
    refill_time: float = Field(default=0.5, ge=0, le=100)
    metric: Literal['euclidean_demo', 'manhattan_demo'] = 'euclidean_demo'
    mode: Literal['schedule', 'fleet'] = 'schedule'
    deadline: float = Field(default=500, gt=0, le=50000)
    time_limit: float = Field(default=12, ge=1, le=60)
    candidates_per_well: int = Field(default=3, ge=1, le=6)

    @model_validator(mode='after')
    def validate_scenario(self):
        if len({w.id for w in self.wells}) != len(self.wells):
            raise ValueError('Los identificadores de pozos deben ser únicos.')
        if len({m.id for m in self.machines}) != len(self.machines):
            raise ValueError('Los identificadores de máquinas deben ser únicos.')
        if set(self.durations) != set(PHASES):
            raise ValueError('Se requieren las siete fases del tratamiento.')
        def valid_duration(v):
            return math.isfinite(v) and 0.1 <= v <= 10000
        if not all(valid_duration(v) for v in self.durations.values()):
            raise ValueError('Cada duración debe estar entre 0.1 y 10000 horas.')
        if len({r.kind for r in self.requirements}) != len(self.requirements):
            raise ValueError('Cada tipo de servicio debe tener una sola ficha de requisitos.')
        if not any(m.kind == 'rig' for m in self.machines):
            raise ValueError('Se necesita al menos una perforadora.')
        for r in self.requirements:
            if not set(r.phases) <= set(PHASES) or len(set(r.phases)) != len(r.phases):
                raise ValueError('Fases de servicio inválidas o repetidas.')
            if r.phases and not any(m.kind == r.kind and m.capacity >= r.demand for m in self.machines):
                raise ValueError(f'Falta un equipo {r.kind} con capacidad suficiente para su demanda.')
        for w in self.wells:
            if not set(w.durations) <= set(PHASES) or 'drill' in w.durations:
                raise ValueError('Las excepciones por pozo no pueden modificar T de perforación.')
            if not all(valid_duration(v) for v in w.durations.values()):
                raise ValueError('Duración individual inválida.')
            demand = self.water_demand if w.water_demand is None else w.water_demand
            if demand > self.tank_capacity:
                raise ValueError(f'{w.id}: el consumo supera el tanque. Esta versión realiza una entrega previa por pozo.')
            if demand and not any(m.kind == 'water' and m.capacity >= demand for m in self.machines):
                raise ValueError(f'{w.id}: falta un camión de agua con capacidad suficiente.')
        for p in [self.depot, *self.wells, *(m.initial for m in self.machines)]:
            if p.x > self.width or p.y > self.height:
                raise ValueError('Todas las coordenadas deben estar dentro del área sintética.')
        for m in self.machines:
            if m.kind == 'water' and m.initial != self.depot:
                raise ValueError('En esta versión los camiones comienzan cargados en la base.')
            if m.kind == 'test' and m.radius != 0:
                raise ValueError('El equipo de ensayo se instala en el pozo: alcance cero.')
        return self

def make_demo(count=6, seed=42) -> Scenario:
    rng = random.Random(seed)
    wells = [Well(id=f'P{i+1:02}', x=round(rng.uniform(130, 920), 1), y=round(rng.uniform(100, 620), 1)) for i in range(count)]
    machines = []
    specs = [('rig', 'D', 2, 0, 1, 1), ('compressor', 'C', 2, 230, 2, 40),
             ('generator', 'G', 2, 280, 2, 80), ('test', 'E', 2, 0, 1, 1), ('water', 'A', 1, 0, 1, 20)]
    for kind, prefix, n, radius, k, q in specs:
        for j in range(n):
            machines.append(Machine(id=f'{prefix}{j+1:02}', kind=kind, initial=Point(x=50, y=50), radius=radius,
                simultaneous=k, capacity=q, setup=0 if kind in ('rig','test','water') else .5,
                disconnect=0 if kind in ('rig','test','water') else .25))
    return Scenario(seed=seed, wells=wells, machines=machines, durations=dict(zip(PHASES, [2,48,4,2,96,24,2])),
        requirements=[Requirement(kind='compressor', phases=['drill','condition'], demand=15),
                      Requirement(kind='generator', phases=['drill','condition','pump'], demand=20),
                      Requirement(kind='fluid', phases=[], demand=10),
                      Requirement(kind='test', phases=list(PHASES[3:]), demand=1)])
