"""One saved-state API example; no game or strength benchmark."""
from pathlib import Path
import copy
import json
import SeanGilbert

def main():
    cases=json.loads((Path(__file__).parent/'examples/saved_states.json').read_text())
    state=cases[0]['state']
    original=copy.deepcopy(state)
    SeanGilbert.configure(seconds=0)
    move=SeanGilbert.getMove(state)
    print(json.dumps({'player':SeanGilbert.name(), 'case':cases[0]['id'],
                      'move':move, 'input_unchanged':state==original}, indent=2))

if __name__=='__main__':
    main()
