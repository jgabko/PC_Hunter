import { formatCurrency, formatDecimal, formatInt } from "../format";

function MetricCard({ label, value }) {
  return (
    <div
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: 8,
        padding: "12px 16px",
        flex: "1 1 200px",
      }}
    >
      <div style={{ fontSize: 13, color: "var(--text-dim)" }}>{label}</div>
      <div style={{ fontSize: 24, fontWeight: 600, color: "var(--accent-blue)" }}>
        {value}
      </div>
    </div>
  );
}

export default function Metrics({ count, rate, avgPrice }) {
  return (
    <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
      <MetricCard label="Itens Filtrados" value={count != null ? formatInt(count) : "—"} />
      <MetricCard
        label="Taxa de Mercado (Dinâmica)"
        value={rate != null ? `R$ ${formatDecimal(rate, 3)}/pt` : "—"}
      />
      <MetricCard
        label="Preço Médio"
        value={avgPrice != null ? formatCurrency(avgPrice) : "—"}
      />
    </div>
  );
}
