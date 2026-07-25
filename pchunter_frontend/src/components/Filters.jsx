const sliderStyle = {
  width: "100%",
  accentColor: "var(--accent-blue)",
};

const fieldStyle = {
  display: "flex",
  flexDirection: "column",
  gap: 6,
};

const labelRowStyle = {
  display: "flex",
  justifyContent: "space-between",
  fontSize: 14,
  color: "var(--text-dim)",
};

export default function Filters({ filters, onChange }) {
  function handle(field, value) {
    onChange({ ...filters, [field]: Number(value) });
  }

  return (
    <div
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: 8,
        padding: "20px 24px",
        display: "flex",
        flexWrap: "wrap",
        gap: 24,
      }}
    >
      <div style={{ ...fieldStyle, flex: "1 1 220px" }}>
        <div style={labelRowStyle}>
          <span>Score Mínimo</span>
          <span>{filters.minScore}</span>
        </div>
        <input
          style={sliderStyle}
          type="range"
          min={0}
          max={50000}
          step={500}
          value={filters.minScore}
          onChange={(e) => handle("minScore", e.target.value)}
        />
      </div>

      <div style={{ ...fieldStyle, flex: "1 1 220px" }}>
        <div style={labelRowStyle}>
          <span>Preço Mínimo</span>
          <span>R$ {filters.minPrice}</span>
        </div>
        <input
          style={sliderStyle}
          type="range"
          min={0}
          max={5000}
          step={50}
          value={filters.minPrice}
          onChange={(e) => handle("minPrice", e.target.value)}
        />
      </div>

      <div style={{ ...fieldStyle, flex: "1 1 220px" }}>
        <div style={labelRowStyle}>
          <span>Preço Máximo</span>
          <span>R$ {filters.maxPrice}</span>
        </div>
        <input
          style={sliderStyle}
          type="range"
          min={100}
          max={10000}
          step={100}
          value={filters.maxPrice}
          onChange={(e) => handle("maxPrice", e.target.value)}
        />
      </div>
    </div>
  );
}
