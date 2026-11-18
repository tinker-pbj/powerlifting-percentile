# Strength Percentile

How your squat, bench, deadlift and total compare with **raw, drug-tested** powerlifters at your bodyweight.

**Live:** https://strengthpercentile.com

## Method
Population: every lifter in [OpenPowerlifting](https://www.openpowerlifting.org) who competed raw, in a drug-tested,
full-power (SBD) meet, aged 16+ (or unknown), not disqualified. Each lifter counts once, at their best result for
that lift, with the bodyweight from that meet.

Percentile of lift `x` at bodyweight `b`:

    percentile(x, b) = Σ wᵢ·[liftᵢ < x] / Σ wᵢ
    wᵢ = exp(−½ · ((ln bwᵢ − ln b) / h)²),  h = 0.035

`h` widens (×1.15 steps) wherever fewer than 1,500 lifters effectively count (Kish effective sample size).
`build.py` tabulates P on a 2.5 kg lift grid for bodyweights spaced 1.5% apart (in hundredths of a percent, so the page can show e.g. 99.87); the page interpolates in lift and log bodyweight. Ties count half.

## Rebuild
    curl -LO https://openpowerlifting.gitlab.io/opl-csv/files/openpowerlifting-latest.zip   # unzip → opl.csv
    python build.py   # needs duckdb + numpy; writes docs/data.json

Data: OpenPowerlifting (public domain). Not affiliated with OpenPowerlifting.
