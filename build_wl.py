"""Olympic weightlifting tables from OpenWeightlifting (public domain), same method as build.py.

Input: the flattened CSV from owl_normalize.py. Each lifter (federation + name + sex) counts once per lift, at their
best result for that lift. Youth categories are left out. Output: docs/wl/data.json.
Usage: python build_wl.py owl.csv
"""
import duckdb, numpy as np, json, sys, math, os

CSV = sys.argv[1] if len(sys.argv) > 1 else 'owl.csv'
H, MIN_EFF, STEP, BW_STEP = 0.035, 1500, 1.0, 0.015
BW_RANGE = {'F': (40, 130), 'M': (50, 175)}
LIFTS = {'total': 'total', 'snatch': 'sn', 'cleanjerk': 'cj'}

con = duckdb.connect(); con.execute("SET memory_limit='1500MB'")
con.execute(f"""CREATE TABLE base AS SELECT fed || ':' || lower(trim(name)) AS who,
    CASE WHEN regexp_matches(lower(coalesce(category,'') || ' ' || coalesce(gender,'')), 'women|female|kvinner|girl') THEN 'F'
         WHEN regexp_matches(lower(coalesce(category,'') || ' ' || coalesce(gender,'')), '\\bmen|male|menn|boy') THEN 'M' END AS sex,
    TRY_CAST(bw AS DOUBLE) bw, TRY_CAST(snatch AS DOUBLE) sn, TRY_CAST(cj AS DOUBLE) cj, TRY_CAST(total AS DOUBLE) total, date
  FROM read_csv('{CSV}', header=true, all_varchar=true)
  WHERE NOT regexp_matches(lower(coalesce(category,'')), 'youth|ungdom|u13|u15|u17|under|school|kid|13-|14-15|16-17')""")
con.execute("""DELETE FROM base WHERE sex IS NULL OR bw IS NULL OR bw NOT BETWEEN 30 AND 250 OR total IS NULL OR total <= 0
  OR sn IS NULL OR sn <= 0 OR cj IS NULL OR cj <= 0 OR abs(sn + cj - total) > 1
  -- typos: nothing above the all-time world records (with a little room)
  OR (sex = 'M' AND (sn > 230 OR cj > 275 OR total > 500)) OR (sex = 'F' AND (sn > 160 OR cj > 200 OR total > 350))""")
snapshot = con.execute("SELECT max(date) FROM base").fetchone()[0]

out = {"meta": {"source": "OpenWeightlifting (public domain)", "latest_meet": str(snapshot), "h": H, "group": "all", "group_label": "All ages",
                "lift_step": STEP, "bw_step_log": BW_STEP, "lifters": {}}, "data": {}}
for sex, (lo, hi) in BW_RANGE.items():
    n_bw = int(math.ceil(math.log(hi / lo) / BW_STEP)) + 1
    bw_grid = lo * np.exp(BW_STEP * np.arange(n_bw))
    out["data"][sex] = {"bw0": lo, "nbw": n_bw, "lifts": {}}
    for lift, col in LIFTS.items():
        r = con.execute(f"""SELECT bw, {col} FROM (SELECT bw, {col}, row_number() OVER (PARTITION BY who ORDER BY {col} DESC, date) rn
              FROM base WHERE sex='{sex}') WHERE rn = 1""").fetchnumpy()
        lbw = np.log(r['bw']); x = r[col]
        o = np.argsort(x); x = x[o]; lbw = lbw[o]
        out["meta"]["lifters"][f"{sex}_{lift}"] = int(len(x))
        g0 = math.floor(np.quantile(x, 0.0001) / STEP) * STEP - STEP
        g1 = math.ceil(x.max() / STEP) * STEP + STEP
        grid = np.arange(g0, g1 + STEP / 2, STEP)
        left = np.searchsorted(x, grid, 'left'); right = np.searchsorted(x, grid, 'right')
        rows, hs, near = [], [], []
        for b in bw_grid:
            h = H
            while True:
                w = np.exp(-0.5 * ((lbw - math.log(b)) / h) ** 2)
                if w.sum() ** 2 / (w ** 2).sum() >= MIN_EFF or h > 0.3: break
                h *= 1.15
            hs.append(round(h, 4)); near.append(int((np.abs(lbw - math.log(b)) <= 1.5 * h).sum()))
            cw = np.concatenate([[0.0], np.cumsum(w)])
            q = np.maximum.accumulate(np.round((cw[left] + 0.5 * (cw[right] - cw[left])) / cw[-1] * 10000).astype(int))
            rows.append([int(q[0])] + np.diff(q).tolist())
        out["data"][sex]["lifts"][lift] = {"x0": g0, "n": len(grid), "rows": rows, "h": hs, "near": near}
        print('wl', sex, lift, len(x), 'grid', g0, g1, len(grid), file=sys.stderr)

os.makedirs('docs/wl', exist_ok=True)
json.dump(out, open('docs/wl/data.json', 'w'), separators=(',', ':'))
