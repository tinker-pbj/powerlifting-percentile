// Strength Percentile: share-link previews.
//
// Sits in front of the static site (GitHub Pages) on the route strengthpercentile.com/*.
// Every request passes through unchanged, except a share link (/?s=M&bw=83&sq=...): for those it works out the
// percentile from the site's own data file and rewrites the page's link-preview tags (title, description, image),
// so iMessage / Discord / Reddit / X show "Top 3% for my bodyweight" instead of the generic card.
// The images are pre-rendered files on the site (/og/M/top-3.png etc). No bindings, secrets or storage.

const SITE = 'https://strengthpercentile.com';
const LB = 0.45359237;
const GROUPS = [['jr', 16, 23, '16–23'], ['open', 24, 39, '24–39'], ['m40', 40, 49, '40–49'], ['m50', 50, 59, '50–59'], ['m60', 60, 200, '60+']];

export default {
  async fetch(request) {
    const url = new URL(request.url);
    // On the live route, fetching our own hostname goes straight to the origin (GitHub Pages).
    // Anywhere else (local testing), fetch from the live site.
    const origin = url.hostname.endsWith('strengthpercentile.com') ? url.origin : SITE;
    const upstream = await fetch(new Request(origin + url.pathname + url.search, request));

    if (request.method !== 'GET' || (url.pathname !== '/' && url.pathname !== '/index.html')) return upstream;
    if (!(upstream.headers.get('content-type') || '').includes('text/html')) return upstream;

    let card;
    try { card = await describe(url.searchParams, origin); } catch { card = null; }
    if (!card) return upstream;

    const set = (value) => ({ element(el) { el.setAttribute('content', value); } });
    const res = new HTMLRewriter()
      .on('meta[property="og:title"]', set(card.title))
      .on('meta[property="og:description"]', set(card.description))
      .on('meta[name="description"]', set(card.description))
      .on('meta[property="og:image"]', set(card.image))
      .on('meta[property="og:url"]', set(SITE + '/' + url.search))
      .transform(upstream);
    const out = new Response(res.body, res);
    out.headers.set('cache-control', 'public, max-age=300');
    return out;
  },
};

// ---- the percentile, computed exactly as the page does it

async function describe(q, origin) {
  const sex = q.get('s') === 'F' ? 'F' : 'M';
  const unit = q.get('u') === 'lb' ? 'lb' : 'kg';
  const num = (k) => { const v = parseFloat(q.get(k)); return isFinite(v) && v > 0 && v < 5000 ? v : null; };
  const toKg = (v) => unit === 'kg' ? v : v * LB;
  const bwU = num('bw');
  const sq = num('sq'), be = num('be'), de = num('de');
  const totU = num('t') ?? (sq && be && de ? sq + be + de : null);
  if (!bwU || !totU) return null;

  const age = num('a');
  const g = age && q.get('c') !== 'all' ? GROUPS.find(([, lo, hi]) => age >= lo && age <= hi) : null;
  const file = `/share/${g ? g[0] : 'all'}-${sex}.json`;   // slim: totals for one sex only
  const r = await fetch(origin + file, { cf: { cacheTtl: 3600, cacheEverything: true } });
  if (!r.ok) return null;
  const D = await r.json();

  const p = percentile(D, sex, toKg(bwU), Math.round(toKg(totU) * 10) / 10);
  const who = (sex === 'M' ? 'men' : 'women') + (g ? ` aged ${g[3]}` : '');
  const fmt = (v) => Math.round(v * 10) / 10;
  const pct = p >= 99.995 ? 'more than 99.99' : p >= 99 ? p.toFixed(2) : p.toFixed(1);
  const t = 100 - p;
  let image = SITE + '/og.png', top = null;
  if (t <= 50) {
    top = t >= 1 ? String(Math.min(50, Math.ceil(t - 1e-9))) : t >= 0.9 ? '1' : String(Math.max(1, Math.ceil(t * 10 - 1e-9)) / 10);
    image = `${SITE}/og/${sex}/top-${top}.png`;
  }
  return {
    title: top ? `Top ${top}% for my bodyweight · Strength Percentile` : 'How strong am I for my bodyweight? · Strength Percentile',
    description: `${fmt(totU).toLocaleString('en-US')} ${unit} total at ${fmt(bwU)} ${unit} bodyweight: stronger than ${pct}% of raw, drug-tested ${who}. How strong are you?`,
    image,
  };
}

function percentile(D, sex, bw, x) {
  const S = D.data[sex], L = S.lifts.total, step = D.meta.bw_step_log;
  const bwMax = S.bw0 * Math.exp(step * (S.nbw - 1));
  const b = Math.min(Math.max(bw, S.bw0), bwMax);
  const i = Math.log(b / S.bw0) / step;
  const a = Math.max(0, Math.min(S.nbw - 2, Math.floor(i))), f = Math.max(0, Math.min(1, i - a));
  const cdf = (k) => { const d = L.rows[k], c = new Float64Array(d.length); let s = 0; for (let j = 0; j < d.length; j++) { s += d[j]; c[j] = s / 100; } return c; };
  const r0 = cdf(a), r1 = cdf(a + 1);
  const t = (x - L.x0) / D.meta.lift_step, n = L.n;
  const at = (k) => r0[k] + f * (r1[k] - r0[k]);
  if (t <= 0) return at(0);
  if (t >= n - 1) return at(n - 1);
  const k = Math.floor(t);
  return at(k) + (t - k) * (at(k + 1) - at(k));
}
