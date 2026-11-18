# Powerlifting Percentile

How your squat, bench, deadlift and total compare with **raw, drug-tested** powerlifters at your bodyweight.

**Live:** https://tinker-pbj.github.io/powerlifting-percentile/

## Method
Population: every lifter in [OpenPowerlifting](https://www.openpowerlifting.org) who competed raw, in a drug-tested,
full-power (SBD) meet, aged 16+ (or unknown), not disqualified. Each lifter counts once, at their best result for
that lift, with the bodyweight from that meet.

Percentile of lift `x` at bodyweight `b`:

    percentile(x, b) = Σ wᵢ·[liftᵢ < x] / Σ wᵢ
    wᵢ = exp(−½ · ((ln bwᵢ − ln b) / h)²),  h = 0.035

`h` widens (×1.15 steps) wherever fewer than 1,500 lifters effectively count (Kish effective sample size).
`build.py` tabulates the 1st–99.9th percentiles at every whole kilo; the page interpolates.

## Rebuild
    curl -LO https://openpowerlifting.gitlab.io/opl-csv/files/openpowerlifting-latest.zip   # unzip → opl.csv
    python build.py   # needs duckdb + numpy; writes docs/data.json

Data: OpenPowerlifting (public domain). Not affiliated with OpenPowerlifting.
