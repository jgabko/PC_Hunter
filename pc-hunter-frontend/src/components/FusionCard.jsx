import { formatCurrency, formatInt } from "../format";

function Column({ label, title, link, price, extra }) {
  return (
    <div style={{ flex: "1 1 200px" }}>
      <div style={{ fontSize: 12, color: "var(--text-dim)", marginBottom: 4 }}>
        {label}
      </div>
      <a
        href={link}
        target="_blank"
        rel="noopener noreferrer"
        style={{
          display: "block",
          fontWeight: 600,
          fontSize: 14,
          color: "var(--text)",
          textDecoration: "none",
          marginBottom: 4,
        }}
      >
        {title}
      </a>
      <div style={{ fontSize: 14, color: "var(--text-dim)" }}>
        {formatCurrency(price)}
      </div>
      {extra && (
        <div style={{ fontSize: 13, color: "var(--text-dim)" }}>{extra}</div>
      )}
    </div>
  );
}

export default function FusionCard({ item }) {
  return (
    <div
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: 8,
        padding: "16px 20px",
        display: "flex",
        flexDirection: "column",
        gap: 12,
      }}
    >
      <div style={{ display: "flex", gap: 24, flexWrap: "wrap" }}>
        <Column
          label="Base"
          title={item.Base_Title}
          link={item.Base_Link}
          price={item.Base_Price}
          extra={item.Base_Is_Office ? "Gabinete office" : null}
        />
        <Column
          label="Doador (GPU)"
          title={item.Donor_Title}
          link={item.Donor_Link}
          price={item.Donor_Price}
          extra={item.Donor_GPU}
        />
        <div style={{ flex: "1 1 200px" }}>
          <div style={{ fontSize: 12, color: "var(--text-dim)", marginBottom: 4 }}>
            Resultado
          </div>
          <div style={{ fontSize: 14 }}>
            Custo total: <strong>{formatCurrency(item.Total_Cost)}</strong>
          </div>
          <div style={{ fontSize: 14 }}>
            Score projetado: <strong>{formatInt(item.Projected_Score)}</strong>
          </div>
          <div style={{ fontSize: 14, color: "#4caf50" }}>
            Lucro estimado: <strong>{formatCurrency(item.Est_Profit)}</strong>
          </div>
        </div>
      </div>

      <div style={{ fontSize: 13, color: "var(--text-dim)" }}>
        Extras necessários: {item.Extra_Details}
      </div>
    </div>
  );
}
