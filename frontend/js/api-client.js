import { getApiBase, getApiKey } from "./config.js";

// chama a api e devolve { ok, status, data, ms, url }
export async function callApi(path, { needsKey = true } = {}) {
  const base = getApiBase();
  const url = `${base}${path.startsWith("/") ? path : `/${path}`}`;
  const headers = { Accept: "application/json" };
  const key = getApiKey();
  if (needsKey && key) headers["X-API-Key"] = key;

  const t0 = performance.now();
  try {
    const res = await fetch(url, { headers });
    const ms = Math.round(performance.now() - t0);
    let data;
    const text = await res.text();
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
    return { ok: res.ok, status: res.status, data, ms, url };
  } catch (err) {
    return {
      ok: false,
      status: 0,
      data: { error: err.message },
      ms: Math.round(performance.now() - t0),
      url,
    };
  }
}
