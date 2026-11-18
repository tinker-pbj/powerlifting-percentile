"""Static lookup tables for agents and scripts: docs/api/v1/*.json (no server needed).

Each file: for one sport, sex and age group, the lift (kg) at each percentile for every whole-kilo bodyweight.
To get a percentile: take the row for your bodyweight and find where your lift falls between the columns.
"""
import json, os, datetime
from pctlib import quantile

P = [float(p) for p in range(1, 100)] + [99.5, 99.9]
SETS = [  # (sport, data file, age group key, label, lifts, bw ranges)
    ('powerlifting', 'docs/data.json', 'all', 'all ages', ['total', 'squat', 'bench', 'deadlift'], {'M': (50, 200), 'F': (40, 150)}),
    *[('powerlifting', f'docs/data-{g}.json', lab, lab, ['total', 'squat', 'bench', 'deadlift'], {'M': (50, 200), 'F': (40, 150)})
      for g, lab in [('jr', '16-23'), ('open', '24-39'), ('m40', '40-49'), ('m50', '50-59'), ('m60', '60plus')]],
    ('weightlifting', 'docs/wl/data.json', 'all', 'all ages', ['total', 'snatch', 'cleanjerk'], {'M': (50, 170), 'F': (40, 125)}),
]
index = []
for sport, f, group, label, lifts, ranges in SETS:
    D = json.load(open(f))
    for sex, word in [('M', 'men'), ('F', 'women')]:
        lo, hi = ranges[sex]
        bws = list(range(lo, hi + 1))
        out = {
            'sport': sport, 'sex': word, 'age_group': label,
            'population': ('raw, drug-tested full-power meets (OpenPowerlifting)' if sport == 'powerlifting' else 'national and international weightlifting meets (OpenWeightlifting)') + ', best result per lifter',
            'units': 'kg', 'updated': datetime.date.today().isoformat(), 'latest_meet': D['meta']['latest_meet'][:10],
            'how_to_use': 'lifts[lift][i][j] is the lift (kg) at percentiles[j] for bodyweight bodyweights_kg[i]. '
                          'Your percentile = interpolate your lift between the two columns it falls between, in the row for your bodyweight. '
                          'Below the first column: under 1st percentile; above the last: over 99.9th.',
            'calculator': 'https://strengthpercentile.com/',
            'percentiles': P, 'bodyweights_kg': bws,
            'lifts': {l: [[round(quantile(D, sex, l, bw, p) * 2) / 2 for p in P] for bw in bws] for l in lifts},
        }
        name = f'{sport}/{word}' + ('' if group == 'all' else f'-{group}') + '.json'
        os.makedirs(os.path.dirname(f'docs/api/v1/{name}'), exist_ok=True)
        json.dump(out, open(f'docs/api/v1/{name}', 'w'), separators=(',', ':'))
        index.append({'sport': sport, 'sex': word, 'age_group': label, 'url': f'https://strengthpercentile.com/api/v1/{name}', 'lifts': lifts})
json.dump({'tables': index, 'docs': 'https://strengthpercentile.com/llms.txt'}, open('docs/api/v1/index.json', 'w'), indent=1)
print(len(index), 'tables')
