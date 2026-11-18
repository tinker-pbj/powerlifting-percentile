var __defProp = Object.defineProperty;
var __name = (target, value) => __defProp(target, "name", { value, configurable: true });

// worker.js
var SITE = "https://strengthpercentile.com";
var LB = 0.45359237;
var GROUPS = [["jr", 16, 23, "16\u201323"], ["open", 24, 39, "24\u201339"], ["m40", 40, 49, "40\u201349"], ["m50", 50, 59, "50\u201359"], ["m60", 60, 200, "60+"]];
var worker_default = {
  async fetch(request) {
    const url = new URL(request.url);
    const origin = url.hostname.endsWith("strengthpercentile.com") ? url.origin : SITE;
    const upstream = await fetch(new Request(origin + url.pathname + url.search, request));
    if (request.method !== "GET" || url.pathname !== "/" && url.pathname !== "/index.html") return upstream;
    if (!(upstream.headers.get("content-type") || "").includes("text/html")) return upstream;
    let card;
    try {
      card = await describe(url.searchParams, origin);
    } catch {
      card = null;
    }
    if (!card) return upstream;
    const set = /* @__PURE__ */ __name((value) => ({ element(el) {
      el.setAttribute("content", value);
    } }), "set");
    const res = new HTMLRewriter().on('meta[property="og:title"]', set(card.title)).on('meta[property="og:description"]', set(card.description)).on('meta[name="description"]', set(card.description)).on('meta[property="og:image"]', set(card.image)).on('meta[property="og:url"]', set(SITE + "/" + url.search)).transform(upstream);
    const out = new Response(res.body, res);
    out.headers.set("cache-control", "public, max-age=300");
    return out;
  }
};
async function describe(q, origin) {
  const sex = q.get("s") === "F" ? "F" : "M";
  const unit = q.get("u") === "lb" ? "lb" : "kg";
  const num = /* @__PURE__ */ __name((k) => {
    const v = parseFloat(q.get(k));
    return isFinite(v) && v > 0 && v < 5e3 ? v : null;
  }, "num");
  const toKg = /* @__PURE__ */ __name((v) => unit === "kg" ? v : v * LB, "toKg");
  const bwU = num("bw");
  const sq = num("sq"), be = num("be"), de = num("de");
  const totU = num("t") ?? (sq && be && de ? sq + be + de : null);
  if (!bwU || !totU) return null;
  const age = num("a");
  const g = age && q.get("c") !== "all" ? GROUPS.find(([, lo, hi]) => age >= lo && age <= hi) : null;
  const file = `/share/${g ? g[0] : "all"}-${sex}.json`;
  const r = await fetch(origin + file, { cf: { cacheTtl: 3600, cacheEverything: true } });
  if (!r.ok) return null;
  const D = await r.json();
  const p = percentile(D, sex, toKg(bwU), Math.round(toKg(totU) * 10) / 10);
  const who = (sex === "M" ? "men" : "women") + (g ? ` aged ${g[3]}` : "");
  const fmt = /* @__PURE__ */ __name((v) => Math.round(v * 10) / 10, "fmt");
  const pct = p >= 99.995 ? "more than 99.99" : p >= 99 ? p.toFixed(2) : p.toFixed(1);
  const t = 100 - p;
  let image = SITE + "/og.png", top = null;
  if (t <= 50) {
    top = t >= 1 ? String(Math.min(50, Math.ceil(t - 1e-9))) : t >= 0.9 ? "1" : String(Math.max(1, Math.ceil(t * 10 - 1e-9)) / 10);
    image = `${SITE}/og/${sex}/top-${top}.png`;
  }
  return {
    title: top ? `Top ${top}% for my bodyweight \xB7 Strength Percentile` : "How strong am I for my bodyweight? \xB7 Strength Percentile",
    description: `${fmt(totU).toLocaleString("en-US")} ${unit} total at ${fmt(bwU)} ${unit} bodyweight: stronger than ${pct}% of raw, drug-tested ${who}. How strong are you?`,
    image
  };
}
__name(describe, "describe");
function percentile(D, sex, bw, x) {
  const S = D.data[sex], L = S.lifts.total, step = D.meta.bw_step_log;
  const bwMax = S.bw0 * Math.exp(step * (S.nbw - 1));
  const b = Math.min(Math.max(bw, S.bw0), bwMax);
  const i = Math.log(b / S.bw0) / step;
  const a = Math.max(0, Math.min(S.nbw - 2, Math.floor(i))), f = Math.max(0, Math.min(1, i - a));
  const cdf = /* @__PURE__ */ __name((k2) => {
    const d = L.rows[k2], c = new Float64Array(d.length);
    let s = 0;
    for (let j = 0; j < d.length; j++) {
      s += d[j];
      c[j] = s / 100;
    }
    return c;
  }, "cdf");
  const r0 = cdf(a), r1 = cdf(a + 1);
  const t = (x - L.x0) / D.meta.lift_step, n = L.n;
  const at = /* @__PURE__ */ __name((k2) => r0[k2] + f * (r1[k2] - r0[k2]), "at");
  if (t <= 0) return at(0);
  if (t >= n - 1) return at(n - 1);
  const k = Math.floor(t);
  return at(k) + (t - k) * (at(k + 1) - at(k));
}
__name(percentile, "percentile");

// ../../../.npm-global/lib/node_modules/wrangler/templates/middleware/middleware-ensure-req-body-drained.ts
var drainBody = /* @__PURE__ */ __name(async (request, env, _ctx, middlewareCtx) => {
  try {
    return await middlewareCtx.next(request, env);
  } finally {
    try {
      if (request.body !== null && !request.bodyUsed) {
        const reader = request.body.getReader();
        while (!(await reader.read()).done) {
        }
      }
    } catch (e) {
      console.error("Failed to drain the unused request body.", e);
    }
  }
}, "drainBody");
var middleware_ensure_req_body_drained_default = drainBody;

// ../../../.npm-global/lib/node_modules/wrangler/templates/middleware/middleware-miniflare3-json-error.ts
function reduceError(e) {
  return {
    name: e?.name,
    message: e?.message ?? String(e),
    stack: e?.stack,
    cause: e?.cause === void 0 ? void 0 : reduceError(e.cause)
  };
}
__name(reduceError, "reduceError");
var jsonError = /* @__PURE__ */ __name(async (request, env, _ctx, middlewareCtx) => {
  try {
    return await middlewareCtx.next(request, env);
  } catch (e) {
    const error = reduceError(e);
    const body = JSON.stringify(error);
    const headers = {
      "Content-Type": "application/json",
      "MF-Experimental-Error-Stack": "true"
    };
    const encoded = encodeURIComponent(body);
    if (encoded.length <= 8192) {
      headers["MF-Experimental-Error-Stack-Payload"] = encoded;
    }
    return new Response(body, { status: 500, headers });
  }
}, "jsonError");
var middleware_miniflare3_json_error_default = jsonError;

// .wrangler/tmp/bundle-pR1Spk/middleware-insertion-facade.js
var __INTERNAL_WRANGLER_MIDDLEWARE__ = [
  middleware_ensure_req_body_drained_default,
  middleware_miniflare3_json_error_default
];
var middleware_insertion_facade_default = worker_default;

// ../../../.npm-global/lib/node_modules/wrangler/templates/middleware/common.ts
var __facade_middleware__ = [];
function __facade_register__(...args) {
  __facade_middleware__.push(...args.flat());
}
__name(__facade_register__, "__facade_register__");
function __facade_invokeChain__(request, env, ctx, dispatch, middlewareChain) {
  const [head, ...tail] = middlewareChain;
  const middlewareCtx = {
    dispatch,
    next(newRequest, newEnv) {
      return __facade_invokeChain__(newRequest, newEnv, ctx, dispatch, tail);
    }
  };
  return head(request, env, ctx, middlewareCtx);
}
__name(__facade_invokeChain__, "__facade_invokeChain__");
function __facade_invoke__(request, env, ctx, dispatch, finalMiddleware) {
  return __facade_invokeChain__(request, env, ctx, dispatch, [
    ...__facade_middleware__,
    finalMiddleware
  ]);
}
__name(__facade_invoke__, "__facade_invoke__");

// .wrangler/tmp/bundle-pR1Spk/middleware-loader.entry.ts
var __Facade_ScheduledController__ = class ___Facade_ScheduledController__ {
  constructor(scheduledTime, cron, noRetry) {
    this.scheduledTime = scheduledTime;
    this.cron = cron;
    this.#noRetry = noRetry;
  }
  scheduledTime;
  cron;
  static {
    __name(this, "__Facade_ScheduledController__");
  }
  #noRetry;
  noRetry() {
    if (!(this instanceof ___Facade_ScheduledController__)) {
      throw new TypeError("Illegal invocation");
    }
    this.#noRetry();
  }
};
function wrapExportedHandler(worker) {
  if (__INTERNAL_WRANGLER_MIDDLEWARE__ === void 0 || __INTERNAL_WRANGLER_MIDDLEWARE__.length === 0) {
    return worker;
  }
  for (const middleware of __INTERNAL_WRANGLER_MIDDLEWARE__) {
    __facade_register__(middleware);
  }
  const fetchDispatcher = /* @__PURE__ */ __name(function(request, env, ctx) {
    if (worker.fetch === void 0) {
      throw new Error("Handler does not export a fetch() function.");
    }
    return worker.fetch(request, env, ctx);
  }, "fetchDispatcher");
  return {
    ...worker,
    fetch(request, env, ctx) {
      const dispatcher = /* @__PURE__ */ __name(function(type, init) {
        if (type === "scheduled" && worker.scheduled !== void 0) {
          const controller = new __Facade_ScheduledController__(
            Date.now(),
            init.cron ?? "",
            () => {
            }
          );
          return worker.scheduled(controller, env, ctx);
        }
      }, "dispatcher");
      return __facade_invoke__(request, env, ctx, dispatcher, fetchDispatcher);
    }
  };
}
__name(wrapExportedHandler, "wrapExportedHandler");
function wrapWorkerEntrypoint(klass) {
  if (__INTERNAL_WRANGLER_MIDDLEWARE__ === void 0 || __INTERNAL_WRANGLER_MIDDLEWARE__.length === 0) {
    return klass;
  }
  for (const middleware of __INTERNAL_WRANGLER_MIDDLEWARE__) {
    __facade_register__(middleware);
  }
  return class extends klass {
    #fetchDispatcher = /* @__PURE__ */ __name((request, env, ctx) => {
      this.env = env;
      this.ctx = ctx;
      if (super.fetch === void 0) {
        throw new Error("Entrypoint class does not define a fetch() function.");
      }
      return super.fetch(request);
    }, "#fetchDispatcher");
    #dispatcher = /* @__PURE__ */ __name((type, init) => {
      if (type === "scheduled" && super.scheduled !== void 0) {
        const controller = new __Facade_ScheduledController__(
          Date.now(),
          init.cron ?? "",
          () => {
          }
        );
        return super.scheduled(controller);
      }
    }, "#dispatcher");
    fetch(request) {
      return __facade_invoke__(
        request,
        this.env,
        this.ctx,
        this.#dispatcher,
        this.#fetchDispatcher
      );
    }
  };
}
__name(wrapWorkerEntrypoint, "wrapWorkerEntrypoint");
var WRAPPED_ENTRY;
if (typeof middleware_insertion_facade_default === "object") {
  WRAPPED_ENTRY = wrapExportedHandler(middleware_insertion_facade_default);
} else if (typeof middleware_insertion_facade_default === "function") {
  WRAPPED_ENTRY = wrapWorkerEntrypoint(middleware_insertion_facade_default);
}
var middleware_loader_entry_default = WRAPPED_ENTRY;
export {
  __INTERNAL_WRANGLER_MIDDLEWARE__,
  middleware_loader_entry_default as default
};
//# sourceMappingURL=worker.js.map
