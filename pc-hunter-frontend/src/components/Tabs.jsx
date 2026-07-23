const TABS = [
  { key: "flips", label: "Upgrades" },
  { key: "fusions", label: "Combinações" },
  { key: "data", label: "Dados" },
];

export default function Tabs({ active, onChange }) {
  return (
    <div
      style={{
        display: "flex",
        gap: 4,
        borderBottom: "1px solid var(--border)",
        marginBottom: 20,
      }}
    >
      {TABS.map((tab) => {
        const isActive = tab.key === active;
        return (
          <button
            key={tab.key}
            onClick={() => onChange(tab.key)}
            style={{
              background: "none",
              border: "none",
              borderBottom: isActive
                ? "2px solid var(--accent-blue)"
                : "2px solid transparent",
              color: isActive ? "var(--text)" : "var(--text-dim)",
              padding: "10px 16px",
              cursor: "pointer",
              fontSize: 15,
              fontWeight: isActive ? 600 : 400,
            }}
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}
