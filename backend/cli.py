import argparse
import json
from pathlib import Path
from .schema import Scenario,make_demo
from .optimizer import solve

def main():
    p=argparse.ArgumentParser(description='Calcula un plan de campaña desde un JSON editable.')
    p.add_argument('--input',type=Path)
    p.add_argument('--output',type=Path,default=Path('plan.json'))
    p.add_argument('--demo',type=int,default=6,help='Número de pozos sintéticos si no se proporciona input')
    p.add_argument('--seed',type=int,default=42)
    args=p.parse_args()
    s=Scenario.model_validate_json(args.input.read_text()) if args.input else make_demo(args.demo,args.seed)
    result=solve(s,lambda p:print(p.get('message',''),p.get('best_hours','')))
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(result['status'],str(args.output))
    if 'makespan' not in result:raise SystemExit(2)

if __name__=='__main__':main()
