"""Synthetic geometry, isolated so real travel/coverage oracles can replace it."""
import math
from .schema import Point, Scenario, Machine

TICKS = 10  # conservative 0.1 h time discretization

def ticks(hours):
    return max(0, math.ceil(hours * TICKS - 1e-8))

def distance(a, b, metric='euclidean_demo'):
    dx, dy = abs(a.x-b.x), abs(a.y-b.y)
    return dx+dy if metric == 'manhattan_demo' else math.hypot(dx,dy)

def travel(a, b, m: Machine, s: Scenario):
    return ticks(distance(a, b, s.metric) / m.speed)

def coordinates(p):
    return {'x': round(p.x, 5), 'y': round(p.y, 5)}

def anchors(s: Scenario, machine: Machine):
    """Data-dependent ungridded candidates, NOT continuous global optimization."""
    points = [Point(x=w.x, y=w.y) for w in s.wells]
    if machine.radius == 0:
        return points
    points += [machine.initial, Point(x=sum(w.x for w in s.wells)/len(s.wells), y=sum(w.y for w in s.wells)/len(s.wells))]
    for i, a in enumerate(s.wells):
        for b in s.wells[i+1:]:
            dx, dy = b.x-a.x, b.y-a.y
            d = math.hypot(dx,dy)
            if 0 < d <= 2*machine.radius:
                mx, my = (a.x+b.x)/2, (a.y+b.y)/2
                points.append(Point(x=mx,y=my))
                h = math.sqrt(max(0,machine.radius**2-(d/2)**2))
                for sign in (-1,1):
                    x,y = mx-sign*h*dy/d, my+sign*h*dx/d
                    if 0 <= x <= s.width and 0 <= y <= s.height:
                        points.append(Point(x=x,y=y))
    unique = {}
    for p in points:
        unique[(round(p.x,5),round(p.y,5))] = p
    return list(unique.values())

def candidates(s, m, well, pool):
    valid = [p for p in pool if distance(p, well) <= m.radius+1e-6]
    valid.sort(key=lambda p: (-sum(distance(p,w) <= m.radius+1e-6 for w in s.wells), distance(p,m.initial,s.metric)))
    # Always keep the well; additional candidates can be anywhere in the area.
    selected = [Point(x=well.x,y=well.y)]
    for p in valid:
        if all(distance(p,q)>1e-5 for q in selected):
            selected.append(p)
        if len(selected) >= s.candidates_per_well:
            break
    return selected[:s.candidates_per_well]

def path(a,b,metric):
    pts = [coordinates(a)]
    if metric == 'manhattan_demo' and a.x != b.x and a.y != b.y:
        pts.append({'x':b.x,'y':a.y})
    pts.append(coordinates(b))
    return pts
