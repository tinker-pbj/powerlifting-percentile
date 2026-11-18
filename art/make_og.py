"""Render the share-preview cards: docs/og/{M,F}/top-{N}.png for N = 1..50 and 0.1..0.9 (percent).
The Worker picks one per share link. Needs rsvg-convert and the Inter font."""
import math, os, subprocess

def card(label, sub, p):
    pts = [(700 + 440 * i / 200, 500 - 260 * math.exp(-0.5 * (-3 + 6 * i / 200) ** 2)) for i in range(201)]
    path = "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    # marker: where the p-th percentile of a normal sits on this curve
    z = math.sqrt(2) * erfinv(2 * p / 100 - 1); z = max(-2.9, min(2.9, z))
    cx = 700 + 440 * (z + 3) / 6; cy = 500 - 260 * math.exp(-0.5 * z * z)
    size = 150 if len(label) <= 7 else 128
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
<rect width="1200" height="630" fill="#0b0b0b"/><rect y="616" width="1200" height="14" fill="#e10b0b"/>
<defs><clipPath id="c"><rect width="{cx:.1f}" height="630"/></clipPath></defs>
<path d="{path}L1140,500L700,500Z" fill="#2a2a2a"/><path d="{path}L1140,500L700,500Z" fill="#e10b0b" opacity=".85" clip-path="url(#c)"/>
<path d="{path}" fill="none" stroke="#fff" stroke-width="4"/>
<line x1="{cx:.1f}" x2="{cx:.1f}" y1="{cy - 70:.1f}" y2="500" stroke="#fff" stroke-width="4"/>
<circle cx="{cx:.1f}" cy="{cy:.1f}" r="11" fill="#e10b0b" stroke="#fff" stroke-width="5"/>
<text x="{cx:.1f}" y="{cy - 84:.1f}" text-anchor="middle" font-family="Inter" font-weight="800" font-size="30" fill="#fff">ME</text>
<text x="64" y="100" font-family="Inter" font-weight="900" font-size="32" letter-spacing="3" fill="#fff">STRENGTH <tspan fill="#e10b0b">PERCENTILE</tspan></text>
<text x="60" y="{250 + size * .55:.0f}" font-family="Inter Display" font-weight="900" font-size="{size}" fill="#e10b0b" letter-spacing="-4">{label}</text>
<text x="64" y="430" font-family="Inter" font-weight="700" font-size="34" fill="#fff">{sub[0]}</text>
<text x="64" y="474" font-family="Inter" font-weight="700" font-size="34" fill="#fff">{sub[1]}</text>
<text x="64" y="572" font-family="Inter" font-weight="800" font-size="30" fill="#a8a8a8">How strong are you? strengthpercentile.com</text>
</svg>'''

def erfinv(y):  # Giles' approximation, plenty for placing a dot
    w = -math.log((1 - y) * (1 + y))
    if w < 5:
        w -= 2.5; p = 2.81022636e-08
        for c in [3.43273939e-07, -3.5233877e-06, -4.39150654e-06, 0.00021858087, -0.00125372503, -0.00417768164, 0.246640727, 1.50140941]: p = c + p * w
    else:
        w = math.sqrt(w) - 3; p = -0.000200214257
        for c in [0.000100950558, 0.00134934322, -0.00367342844, 0.00573950773, -0.0076224613, 0.00943887047, 1.00167406, 2.83297682]: p = c + p * w
    return p * y

tops = [n for n in range(1, 51)] + [n / 10 for n in range(1, 10)]
for sport, folder in [('pl', 'docs/og'), ('wl', 'docs/og/wl')]:
    for sex, who in [('M', 'men'), ('F', 'women')]:
        os.makedirs(f'{folder}/{sex}', exist_ok=True)
        group = f'raw, tested {who}' if sport == 'pl' else ('male' if sex == 'M' else 'female') + ' weightlifters'
        for t in tops:
            name = f'{t:g}'
            pct = f'{100 - t:g}' if t >= 1 else f'{100 - t:.1f}'
            svg = card(f'TOP {name}%', ('for my bodyweight, stronger than', f'{pct}% of {group}'), 100 - t)
            subprocess.run(['rsvg-convert', '-o', f'{folder}/{sex}/top-{name}.png'], input=svg.encode(), check=True)
print('ok')
