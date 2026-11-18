"""Build percentile tables from OpenPowerlifting: raw, drug-tested, full-power (SBD) meets.

Population: lifters aged 16+ (or unknown), not disqualified. Each lifter counts once per lift, at their best
result for that lift, with the bodyweight they weighed at that meet.

Percentile of lift x at bodyweight b:
    P(x, b) = (Σ wᵢ·[liftᵢ < x] + ½·Σ wᵢ·[liftᵢ = x]) / Σ wᵢ
    wᵢ = exp(−½ · ((ln bwᵢ − ln b) / h)²),  h = 0.035, widened ×1.15 until the Kish effective n ≥ 1500.

Output (docs/data.json): for each sex and lift, P on a grid of lifts (every 2.5 kg) for a log-spaced grid of
bodyweights (every 1.5%), in hundredths of a percent, delta-encoded along the lift axis. The page interpolates
linearly in lift and in log bodyweight.

Usage: python build.py path/to/openpowerlifting.csv
"""
import duckdb, numpy as np, json, sys, math, os

CSV = sys.argv[1] if len(sys.argv) > 1 else 'opl.csv'
H, MIN_EFF, STEP, BW_STEP = 0.035, 1500, 2.5, 0.015
BW_RANGE = {'F': (40, 170), 'M': (50, 230)}
LIFTS = {'total': 'tot', 'squat': 'sq', 'bench': 'bp', 'deadlift': 'dl'}

con = duckdb.connect(); con.execute("SET memory_limit='1500MB'")
con.execute(f"""CREATE TABLE base AS SELECT Name, Sex, BodyweightKg::DOUBLE bw, Best3SquatKg::DOUBLE sq,
  Best3BenchKg::DOUBLE bp, Best3DeadliftKg::DOUBLE dl, TotalKg::DOUBLE tot, Date,
  -- age: exact if known, else the AgeClass range when it falls inside one group
  COALESCE(Age::DOUBLE, CASE WHEN AgeClass IS NOT NULL THEN
     CASE WHEN TRY_CAST(split_part(AgeClass,'-',2) AS DOUBLE) <= 23 THEN 20
          WHEN TRY_CAST(split_part(AgeClass,'-',1) AS DOUBLE) >= 24 AND TRY_CAST(split_part(AgeClass,'-',2) AS DOUBLE) <= 39 THEN 30
          WHEN TRY_CAST(split_part(AgeClass,'-',1) AS DOUBLE) >= 40 AND TRY_CAST(split_part(AgeClass,'-',2) AS DOUBLE) <= 49 THEN 45
          WHEN TRY_CAST(split_part(AgeClass,'-',1) AS DOUBLE) >= 50 AND TRY_CAST(split_part(AgeClass,'-',2) AS DOUBLE) <= 59 THEN 55
          WHEN TRY_CAST(split_part(AgeClass,'-',1) AS DOUBLE) >= 60 THEN 65 END END) AS age
  FROM read_csv('{CSV}', header=true, all_varchar=true)
  WHERE Equipment='Raw' AND Tested='Yes' AND Event='SBD' AND Sex IN ('M','F')
    AND BodyweightKg::DOUBLE BETWEEN 30 AND 250 AND TotalKg::DOUBLE > 0
    AND Place NOT IN ('DQ','DD','NS','G') AND (Age IS NULL OR Age::DOUBLE >= 16)
    AND NOT (Age IS NULL AND COALESCE(TRY_CAST(split_part(AgeClass,'-',2) AS DOUBLE), 99) < 16)""")
snapshot = con.execute("SELECT max(Date) FROM base").fetchone()[0]

GROUPS = {  # key: (label, min age, max age), None = everyone (age known or not)
    'all': ('All ages', None, None), 'jr': ('16–23', 16, 23), 'open': ('24–39', 24, 39),
    'm40': ('40–49', 40, 49), 'm50': ('50–59', 50, 59), 'm60': ('60+', 60, 200)}
for gkey, (glabel, amin, amax) in GROUPS.items():
    gwhere = '' if amin is None else f' AND age BETWEEN {amin} AND {amax + 0.999}'
    out = {"meta": {"source": "OpenPowerlifting (public domain)", "latest_meet": str(snapshot), "h": H, "group": gkey, "group_label": glabel,
                    "lift_step": STEP, "bw_step_log": BW_STEP, "lifters": {}}, "data": {}}
    for sex, (lo, hi) in BW_RANGE.items():
        n_bw = int(math.ceil(math.log(hi / lo) / BW_STEP)) + 1
        bw_grid = lo * np.exp(BW_STEP * np.arange(n_bw))
        out["data"][sex] = {"bw0": lo, "nbw": n_bw, "lifts": {}}
        for lift, col in LIFTS.items():
            r = con.execute(f"""SELECT bw, {col} FROM (SELECT bw, {col},
                  row_number() OVER (PARTITION BY Name ORDER BY {col} DESC, Date) rn FROM base WHERE Sex='{sex}' AND {col} > 0{gwhere})
                WHERE rn = 1""").fetchnumpy()
            lbw = np.log(r['bw']); x = r[col]
            min_eff = min(MIN_EFF, max(300, len(x) // 8))   # small groups (e.g. women 60+) get a smaller floor
            o = np.argsort(x); x = x[o]; lbw = lbw[o]
            out["meta"]["lifters"][f"{sex}_{lift}"] = int(len(x))
            # common lift grid for this sex/lift: from the 0.01st percentile of all lifters to past the strongest one
            g0 = math.floor(np.quantile(x, 0.0001) / STEP) * STEP - STEP
            g1 = math.ceil(x.max() / STEP) * STEP + STEP   # past the strongest lifter: P reaches 100 at every bodyweight
            grid = np.arange(g0, g1 + STEP / 2, STEP)
            left = np.searchsorted(x, grid, 'left'); right = np.searchsorted(x, grid, 'right')
            rows = []; hs = []; near = []
            for b in bw_grid:
                h = H
                while True:
                    w = np.exp(-0.5 * ((lbw - math.log(b)) / h) ** 2)
                    if w.sum() ** 2 / (w ** 2).sum() >= min_eff or h > 0.3: break
                    h *= 1.15
                hs.append(round(h, 4)); near.append(int((np.abs(lbw - math.log(b)) <= 1.5 * h).sum()))
                cw = np.concatenate([[0.0], np.cumsum(w)]); tot = cw[-1]
                p = (cw[left] + 0.5 * (cw[right] - cw[left])) / tot          # tie-aware CDF at each grid lift
                q = np.round(p * 10000).astype(int)                          # hundredths of a percent
                q = np.maximum.accumulate(q)
                rows.append([int(q[0])] + np.diff(q).tolist())
            out["data"][sex]["lifts"][lift] = {"x0": g0, "n": len(grid), "rows": rows, "h": hs, "near": near}
            print(gkey, sex, lift, len(x), "grid", g0, g1, len(grid), "min_eff", min_eff, file=sys.stderr)

    json.dump(out, open('docs/data.json' if gkey == 'all' else f'docs/data-{gkey}.json', 'w'), separators=(',', ':'))
    # slim per-sex totals for the share-preview Worker (it has a tight CPU budget)
    os.makedirs('docs/share', exist_ok=True)
    for sex, S in out["data"].items():
        T = S["lifts"]["total"]
        slim = {"meta": {"bw_step_log": BW_STEP, "lift_step": STEP},
                "data": {sex: {"bw0": S["bw0"], "nbw": S["nbw"], "lifts": {"total": {"x0": T["x0"], "n": T["n"], "rows": T["rows"]}}}}}
        json.dump(slim, open(f'docs/share/{gkey}-{sex}.json', 'w'), separators=(',', ':'))
