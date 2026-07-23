import { formatCurrency } from "../format";

const TYPE_LABELS = {
  FALTA_GPU: { label: "Falta GPU", color: "#ff9f43" },
  ACHADO_BARATO: { label: "Achado Barato", color: "#4c8dff" },
};

export default function FlipCard({ item }) {
  const typeInfo = TYPE_LABELS[item.type] || { label: item.type, color: "var(--text-dim)" };

  return (
    <div
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: 8,
        padding: "16px 20px",
        display: "flex",
        flexDirection: "column",
        gap: 8,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
        <a
          href={item.link}
          target="_blank"
          rel="noopener noreferrer"
          style={{ fontWeight: 600, fontSize: 15, color: "var(--text)", textDecoration: "none" }}
        >
          {item.title}
        </a>
        <span
          style={{
            fontSize: 12,
            fontWeight: 600,
            color: typeInfo.color,
            border: `1px solid ${typeInfo.color}`,
            borderRadius: 999,
            padding: "2px 10px",
            whiteSpace: "nowrap",
          }}
        >
          {typeInfo.label}
        </span>
      </div>

      <p style={{ margin: 0, fontSize: 14, color: "var(--text-dim)" }}>{item.strategy}</p>

      <div style={{ display: "flex", gap: 24, marginTop: 8 }}>
        <div>
          <div style={{ fontSize: 12, color: "var(--text-dim)" }}>Preço Atual</div>
          <div style={{ fontSize: 18, fontWeight: 600 }}>
            {formatCurrency(item.current_price)}
          </div>
        </div>
        <div>
          <div style={{ fontSize: 12, color: "var(--text-dim)" }}>Lucro Estimado</div>
          <div style={{ fontSize: 18, fontWeight: 600, color: "#4caf50" }}>
            {formatCurrency(item.est_profit)}
          </div>
        </div>
      </div>
    </div>
  );
}
