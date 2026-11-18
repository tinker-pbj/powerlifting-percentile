"""Flatten OpenWeightlifting's event_data/*/*.csv (several column layouts) into one CSV:
fed,date,category,gender,name,bw,snatch,cj,total"""
import csv, glob, os, sys
root = sys.argv[1] if len(sys.argv) > 1 else 'owl/event_data'
out = csv.writer(open(sys.argv[2] if len(sys.argv) > 2 else 'owl.csv', 'w', newline=''))
out.writerow(['fed', 'date', 'category', 'gender', 'name', 'bw', 'snatch', 'cj', 'total'])
pick = lambda r, *ks: next((r[k] for k in ks if k in r and r[k] not in (None, '')), '')
n = 0
for path in glob.glob(os.path.join(root, '*', '*.csv')):
    fed = path.split(os.sep)[-2]
    with open(path, newline='', encoding='utf-8', errors='replace') as f:
        for r in csv.DictReader(f):
            out.writerow([fed, pick(r, 'date'), pick(r, 'age_category', 'category'), pick(r, 'gender'),
                          pick(r, 'lifter', 'lifter_name'), pick(r, 'body_weight_(kg)', 'bodyweight'),
                          pick(r, 'best_snatch'), pick(r, 'best_c&j', 'best_cj'), pick(r, 'total')]); n += 1
print(n, file=sys.stderr)
