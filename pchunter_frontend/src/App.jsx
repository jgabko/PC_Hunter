import { useEffect, useState } from "react";
import { api } from "./api";
import { useDebouncedValue } from "./hooks/useDebouncedValue";
import Filters from "./components/Filters";
import Metrics from "./components/Metrics";

const DEFAULT_FILTERS = {
  minScore: 3000,
  minPrice: 200,
  maxPrice: 4000,
};

export default function App() {
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const debouncedFilters = useDebouncedValue(filters, 400);

  const [market, setMarket] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    setError(null);
    api
      .getMarket(debouncedFilters)
      .then((data) => setMarket(data))
      .catch((err) =>
        setError(
          `Não foi possível carregar os dados (${err.message}). A API está rodando em http://localhost:8000?`
        )
      )
      .finally(() => setLoading(false));
  }, [debouncedFilters]);

  return (
    <div style={{ padding: "32px 48px", maxWidth: 1100, margin: "0 auto" }}>
      <h1 style={{ color: "var(--accent-blue)", marginBottom: 4 }}>OLX PC Hunter</h1>
      <p style={{ color: "var(--text-dim)", marginTop: 0, marginBottom: 24 }}>
        Margens aplicadas: -15% na venda (negociação) | +R$ 50 de custo
        operacional (deslocamento/pasta térmica)
      </p>

      <div style={{ marginBottom: 20 }}>
        <Filters filters={filters} onChange={setFilters} />
      </div>

      <div style={{ marginBottom: 24 }}>
        <Metrics
          count={market?.count}
          rate={market?.rate}
          avgPrice={market?.avg_price}
        />
      </div>

      {error && (
        <div
          style={{
            background: "var(--surface)",
            border: "1px solid var(--danger)",
            borderLeft: "3px solid var(--danger)",
            borderRadius: 8,
            padding: "16px 20px",
            marginBottom: 24,
          }}
        >
          {error}
        </div>
      )}

      {loading && !market && (
        <p style={{ color: "var(--text-dim)" }}>Carregando dados do mercado...</p>
      )}

      {market && market.count === 0 && !loading && (
        <p style={{ color: "var(--text-dim)" }}>
          Banco de dados vazio ou nenhum item nesse filtro. Rode o scraper
          (python pipeline.py) ou ajuste os filtros acima.
        </p>
      )}

      {/* As abas de Upgrades / Combinações / Dados entram nas próximas etapas */}
    </div>
  );
}
