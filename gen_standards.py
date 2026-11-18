"""Static strength-standards pages (crawlable, no JavaScript), generated from the same tables as the calculator.

docs/standards/index.html and docs/standards/{powerlifting,weightlifting}/{men,women}/{class}/index.html, plus
docs/sitemap.xml. Run after build.py and build_wl.py.
"""
import json, math, os, html, datetime

SITE = 'https://strengthpercentile.com'
LB = 0.45359237
PCTS = [10, 25, 50, 75, 90, 95, 99]
SPORTS = {
    'powerlifting': {'file': 'docs/data.json', 'lifts': [('squat', 'Squat'), ('bench', 'Bench press'), ('deadlift', 'Deadlift'), ('total', 'Total')],
                     'round': 2.5, 'who': 'raw, drug-tested powerlifters', 'param': '',
                     'classes': {'M': [59, 66, 74, 83, 93, 105, 120, '120+'], 'F': [47, 52, 57, 63, 69, 76, 84, '84+']},
                     'plus_bw': {'M': 135, 'F': 100}},
    'weightlifting': {'file': 'docs/wl/data.json', 'lifts': [('snatch', 'Snatch'), ('cleanjerk', 'Clean & jerk'), ('total', 'Total')],
                      'round': 1, 'who': 'competitive weightlifters', 'param': 'sp=wl&',
                      'classes': {'M': [60, 65, 71, 79, 88, 94, 110, '110+'], 'F': [48, 53, 58, 63, 69, 77, 86, '86+']},
                      'plus_bw': {'M': 125, 'F': 100}},
}
SEX = {'M': ('men', 'Men'), 'F': ('women', 'Women')}


def quantile(D, sex, lift, bw, p):
    S = D['data'][sex]; L = S['lifts'][lift]; st = D['meta']['bw_step_log']
    i = math.log(bw / S['bw0']) / st
    a = max(0, min(S['nbw'] - 2, math.floor(i))); f = max(0.0, min(1.0, i - a))
    def cdf(k):
        s, out = 0, []
        for d in L['rows'][k]: s += d; out.append(s / 100)
        return out
    r0, r1 = cdf(a), cdf(a + 1)
    c = [r0[k] + f * (r1[k] - r0[k]) for k in range(L['n'])]
    k = 0
    while k < len(c) - 1 and c[k + 1] < p: k += 1
    span = c[k + 1] - c[k] if k + 1 < len(c) else 0
    return L['x0'] + D['meta']['lift_step'] * (k + ((p - c[k]) / span if span > 0 else 0))


def rnd(x, step): return round(x / step) * step
def kg(x): return f'{x:g}'
def lb(x): return f'{round(x / LB / 5) * 5:,.0f}'

CSS = """*{box-sizing:border-box}body{margin:0;background:#f3f3f3;color:#0b0b0b;font:16px/1.55 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.band{background:#0b0b0b;border-bottom:3px solid #e10b0b}.band a{display:block;max-width:900px;margin:0 auto;padding:14px 20px;color:#fff;text-decoration:none;font-weight:900;letter-spacing:.04em;text-transform:uppercase}.band b{color:#e10b0b}
main{max-width:900px;margin:0 auto;padding:22px 20px 60px}h1{font-size:clamp(1.4rem,4vw,2rem);letter-spacing:-.02em;margin:6px 0 6px}h2{font-size:1.15rem;margin:28px 0 8px}
p{max-width:70ch}.mut{color:#6e6e6e}a{color:#e10b0b}.crumb{font-size:.88rem;color:#6e6e6e}.crumb a{color:inherit}
.card{background:#fff;border:1px solid #e3e3e3;border-radius:16px;padding:6px 18px 14px;margin:14px 0;overflow-x:auto}
table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums;min-width:520px}th,td{text-align:right;padding:9px 8px;border-bottom:1px solid #eee}th:first-child,td:first-child{text-align:left}
thead th{font-size:.8rem;text-transform:uppercase;letter-spacing:.06em;color:#6e6e6e}td small{color:#6e6e6e;display:block;font-size:.78rem}
.cta{display:inline-block;background:#e10b0b;color:#fff;text-decoration:none;font-weight:800;padding:11px 18px;border-radius:99px;margin:8px 0}
.classes{display:flex;flex-wrap:wrap;gap:8px;padding:0;list-style:none}.classes a{display:block;padding:7px 12px;border-radius:10px;background:#fff;border:1px solid #e3e3e3;color:#0b0b0b;text-decoration:none;font-weight:700}
.classes a.on{background:#0b0b0b;color:#fff}footer{color:#6e6e6e;font-size:.8rem;margin-top:30px}footer a{color:inherit}"""

def page(title, desc, path, body):
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title><meta name="description" content="{html.escape(desc)}"><link rel="canonical" href="{SITE}{path}">
<meta property="og:title" content="{html.escape(title)}"><meta property="og:description" content="{html.escape(desc)}"><meta property="og:image" content="{SITE}/og.png"><meta name="twitter:card" content="summary_large_image">
<style>{CSS}</style></head><body><div class="band"><a href="/">Strength <b>Percentile</b></a></div><main>{body}
<footer>Data: <a href="https://www.openpowerlifting.org">OpenPowerlifting</a> and <a href="https://www.openweightlifting.org">OpenWeightlifting</a> (public domain), refreshed weekly. Not affiliated with either. · <a href="/standards/">All strength standards</a> · <a href="/">Calculator</a></footer>
</main><script defer src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon='{{"token": "472b7ce3b3a14314816f2c2c47df804c"}}'></script></body></html>"""

def cls_label(c): return f'{c}+ kg' if isinstance(c, str) else f'{c} kg'
def cls_slug(c): return f'{c.rstrip("+")}plus-kg' if isinstance(c, str) else f'{c}kg'

urls = [('/', '1.0'), ('/standards/', '0.9')]
index_parts = []
for sport, cfg in SPORTS.items():
    D = json.load(open(cfg['file']))
    for sex in ['M', 'F']:
        word, Word = SEX[sex]
        classes = cfg['classes'][sex]
        links = []
        for c in classes:
            links.append((c, f'/standards/{sport}/{word}/{cls_slug(c)}/'))
        index_parts.append(f'<h2>{Word}: {sport}</h2><ul class="classes">' + ''.join(f'<li><a href="{u}">{cls_label(c)}</a></li>' for c, u in links) + '</ul>')
        for c, url in links:
            bw = cfg['plus_bw'][sex] if isinstance(c, str) else c
            bw_txt = f'{cls_label(c)} class' + (f' (about {bw} kg / {round(bw / LB)} lb)' if isinstance(c, str) else f' ({round(bw / LB)} lb)')
            rows = []
            summary = {}
            for lift, name in cfg['lifts']:
                vals = [rnd(quantile(D, sex, lift, bw, p), cfg['round']) for p in PCTS]
                summary[lift] = vals
                rows.append(f'<tr><td><b>{html.escape(name)}</b></td>' + ''.join(f'<td>{kg(v)} kg<small>{lb(v)} lb</small></td>' for v in vals) + '</tr>')
            main_lifts = [l for l, _ in cfg['lifts'] if l != 'total']
            med = summary['total'][PCTS.index(50)]; p90 = summary['total'][PCTS.index(90)]
            title = f"Strength standards for {word} at {cls_label(c)}: {sport} percentiles"
            desc = (f"What's a good {'/'.join(n.lower() for _, n in cfg['lifts'][:-1])} for {word} weighing {cls_label(c)}? "
                    f"Median total {kg(med)} kg ({lb(med)} lb), 90th percentile {kg(p90)} kg, from real {cfg['who']}.")
            nav = '<ul class="classes">' + ''.join(f'<li><a href="{u}"{" class=on" if cc == c else ""}>{cls_label(cc)}</a></li>' for cc, u in links) + '</ul>'
            calc = f"/?{cfg['param']}s={sex}&u=kg&bw={bw}"
            body = f"""<div class="crumb"><a href="/standards/">Strength standards</a> › {sport.title()} › {Word}</div>
<h1>{Word}, {cls_label(c)}: {sport} strength standards</h1>
<p>How {cfg['who']} in the {bw_txt} compare. Each number is the best lift at that percentile among {word} near this bodyweight: e.g. the <b>90th percentile</b> column is stronger than 90% of them. The median total here is <b>{kg(med)} kg ({lb(med)} lb)</b>.</p>
<div class="card"><table><thead><tr><th>Lift</th>{''.join(f'<th>{p}th</th>' if p != 50 else '<th>Median</th>' for p in PCTS)}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<a class="cta" href="{calc}">Calculate your exact percentile →</a>
<h2>Other weight classes</h2>{nav}
<h2>How these are calculated</h2>
<p class="mut">From OpenPowerlifting / OpenWeightlifting meet results{', raw and drug-tested only' if sport == 'powerlifting' else ''}. Each lifter counts once, at their best result, and lifters closer to {bw} kg bodyweight count more (a bell curve about ±3.5% wide). Percentiles are among people who compete, a strong crowd.</p>"""
            os.makedirs('docs' + url, exist_ok=True)
            open('docs' + url + 'index.html', 'w').write(page(title, desc, url, body))
            urls.append((url, '0.7'))

body = ('<div class="crumb"><a href="/">Calculator</a></div><h1>Strength standards by weight class</h1>'
        '<p>Squat, bench, deadlift, snatch and clean &amp; jerk percentiles for men and women in every weight class, from real meet results. '
        'Pick a class, or <a href="/">calculate your exact percentile</a>.</p>' + ''.join(index_parts))
os.makedirs('docs/standards', exist_ok=True)
open('docs/standards/index.html', 'w').write(page('Strength standards by weight class: powerlifting and weightlifting',
     'Squat, bench, deadlift, snatch and clean & jerk standards for men and women in every weight class, from real competition results.', '/standards/', body))

today = datetime.date.today().isoformat()
open('docs/sitemap.xml', 'w').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
    ''.join(f'  <url><loc>{SITE}{u}</loc><lastmod>{today}</lastmod><priority>{p}</priority></url>\n' for u, p in urls) + '</urlset>\n')
print(len(urls), 'urls')
