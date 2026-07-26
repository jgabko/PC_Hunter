// Em produção (Vercel), configure VITE_API_URL com a URL da API no Render
// (ex: https://pc-hunter.onrender.com). Sem essa variável, cai no localhost
// de dev — é assim que funciona hoje com `npm run dev` + `uvicorn` local.
const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path) {
  const res = await fetch(`${BASE_URL}${path}`);
  if (!res.ok) {
    throw new Error(`Erro ${res.status} ao chamar ${path}`);
  }
  return res.json();
}

function toQuery(filters) {
  const params = new URLSearchParams();
  if (filters?.minScore != null) params.set("min_score", filters.minScore);
  if (filters?.minPrice != null) params.set("min_price", filters.minPrice);
  if (filters?.maxPrice != null) params.set("max_price", filters.maxPrice);
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

export const api = {
  health: () => request("/health"),
  getMarket: (filters) => request(`/market${toQuery(filters)}`),
  getFlips: (filters) => request(`/flips${toQuery(filters)}`),
  getFusions: (filters) => request(`/fusions${toQuery(filters)}`),
};