"""Validate and summarize curated historical selection results."""
from collections import Counter, defaultdict
from pathlib import Path
import json

def summarize(rows):
    if not rows:
        raise ValueError('No historical results supplied')
    seen=set(); pairs=defaultdict(list)
    opponents=defaultdict(Counter); colors=defaultdict(Counter)
    stages=defaultdict(Counter); boards=set(); totals=Counter()
    for row in rows:
        identifier=row['id']
        if identifier in seen:
            raise ValueError('Duplicate game ID: '+identifier)
        seen.add(identifier)
        players=row['players']; scores=row['scores']
        if set(players)!={'Light','Dark'} or list(players.values()).count('denial')!=1:
            raise ValueError('Each row must contain exactly one denial player')
        if set(scores)!={'Light','Dark'} or any(type(v) is not int or v<0 for v in scores.values()):
            raise ValueError('Scores must be nonnegative integers for both colors')
        winner_color='Light' if scores['Light']>=scores['Dark'] else 'Dark'
        if row['winner_color']!=winner_color or row['winner']!=players[winner_color]:
            raise ValueError('Winner disagrees with final scores and Light tie rule')
        if type(row['plies']) is not int or row['plies']<=0:
            raise ValueError('Plies must be a positive integer')
        color=next(k for k,v in players.items() if v=='denial')
        opponent=next(v for v in players.values() if v!='denial')
        outcome='wins' if row['winner']=='denial' else 'losses'
        pairs[(opponent,row['board'])].append(color)
        opponents[opponent][outcome]+=1; colors[color][outcome]+=1
        stages['random_extension' if identifier.startswith('r') else 'earlier'][outcome]+=1
        totals[outcome]+=1; boards.add(row['board'])
    if any(sorted(pair)!=['Dark','Light'] for pair in pairs.values()):
        raise ValueError('Each opponent/board pair must contain one game in each color')
    counts=lambda values:{key:{'wins':v['wins'],'losses':v['losses']} for key,v in sorted(values.items())}
    return {'games':len(rows),'wins':totals['wins'],'losses':totals['losses'],
            'boards':len(boards),'opponents':counts(opponents),'colors':counts(colors),
            'stages':counts(stages),
            'scope':'Historical selected internal sample; no new games or general win probability.'}

def main():
    data=Path(__file__).resolve().parents[1]/'evidence/selection_games.json'
    print(json.dumps(summarize(json.loads(data.read_text())),indent=2))

if __name__=='__main__':
    main()
