"""Build percentile tables from OpenPowerlifting: raw, drug-tested, full-power (SBD) meets.
Per lifter, keep their best result for each lift (with the bodyweight they weighed at that meet).
Percentile at bodyweight b = kernel-weighted share of lifters whose best is below X, with Gaussian weights on log-bodyweight."""
import duckdb, numpy as np, json, sys
con = duckdb.connect(); con.execute("SET memory_limit='1500MB'")
CSV = sys.argv[1] if len(sys.argv) > 1 else 'opl.csv'
src = f"""(SELECT Name, Sex, Event, Equipment, Age, BodyweightKg AS bw, Best3SquatKg AS sq, Best3BenchKg AS bp,
  Best3DeadliftKg AS dl, TotalKg AS tot, Place, Tested='Yes' AS Tested, Date
  FROM read_csv('{CSV}', header=true, all_varchar=true))"""
base = f"""SELECT Name, Sex, bw::DOUBLE bw, sq::DOUBLE sq, bp::DOUBLE bp, dl::DOUBLE dl, tot::DOUBLE tot, Date FROM {src}
  WHERE Equipment='Raw' AND Tested AND Event='SBD' AND Sex IN ('M','F')
    AND bw::DOUBLE BETWEEN 30 AND 250 AND tot::DOUBLE > 0
    AND Place NOT IN ('DQ','DD','NS','G')
    AND (Age IS NULL OR Age::DOUBLE >= 16)"""
LIFTS = {'total':'tot','squat':'sq','bench':'bp','deadlift':'dl'}
P = np.concatenate([np.arange(1,99,1.0), np.arange(99,99.91,0.1)])  # percentiles to tabulate
H = 0.035   # kernel width on ln(bodyweight): ~±3.5% bodyweight
MIN_EFF = 1500  # widen the kernel where data is thin until this many effective lifters
out = {"meta": {}, "p": [round(x,1) for x in P.tolist()], "tables": {}}
for sex, (lo, hi) in {'F': (40, 150), 'M': (50, 200)}.items():
    for lift, col in LIFTS.items():
        rows = con.execute(f"""SELECT bw, {col} FROM (
            SELECT bw, {col}, row_number() OVER (PARTITION BY Name ORDER BY {col} DESC, Date) rn
            FROM ({base}) WHERE Sex='{sex}' AND {col} > 0) WHERE rn=1""").fetchnumpy()
        bw = np.log(rows['bw'].astype(float)); x = rows[col].astype(float)
        order = np.argsort(x); x = x[order]; bw = bw[order]
        grid = np.arange(lo, hi+1, 1.0); table = []; effs = []; hs = []
        for b in grid:
            h = H
            while True:
                w = np.exp(-0.5*((bw - np.log(b))/h)**2)
                eff = w.sum()**2 / (w**2).sum()
                if eff >= MIN_EFF or h > 0.3: break
                h *= 1.15
            cw = np.cumsum(w); cw /= cw[-1]
            q = np.interp(P/100, cw, x)
            table.append(np.round(q, 1).tolist()); effs.append(int(eff)); hs.append(round(h,3))
        out["tables"][f"{sex}_{lift}"] = {"bw0": lo, "rows": table}
        out["meta"][f"{sex}_{lift}"] = {"lifters": int(len(x)), "eff_min": min(effs), "h_max": max(hs)}
        print(sex, lift, len(x), "eff range", min(effs), max(effs), "h max", max(hs), file=sys.stderr)
out["meta"]["source"] = "OpenPowerlifting 2026-11-14 (public domain), raw + tested, SBD meets, best result per lifter"
json.dump(out, open('docs/data.json','w'), separators=(',',':'))
