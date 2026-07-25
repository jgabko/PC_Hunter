import { useMemo, useState } from "react";
import { formatCurrency, formatDecimal, formatInt } from "../format";

const COLUMNS = [
  { key: "title", label: "Título" },
  { key: "price", label: "Preço (R$)" },
  { key: "cpu_score", label: "Score CPU" },
  { key: "gpu_score", label: "Score GPU" },
  { key: "system_score", label: "Score Total" },
  { key: "value_ratio", label: "Custo-Benefício" },
];

const cellStyle = {
  padding: "8px 12px",
  borderBottom: "1px solid var(--border)",
  fontSize: 14,
};

export default function DataTable({ items }) {
  const [sortKey, setSortKey] = useState("system_score");
  const [sortDir, setSortDir] = useState("desc");

  const sorted = useMemo(() => {
    if (!items) return [];
    const copy = [...items];
    copy.sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      if (av == null) return 1;
      if (bv == null) return -1;
      if (typeof av === "string") {
        return sortDir === "asc" ? av.localeCompare(bv) : bv.localeCompare(av);
      }
      return sortDir === "asc" ? av - bv : bv - av;
    });
    return copy;
  }, [items, sortKey, sortDir]);

  function handleSort(key) {
    if (key === sortKey) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  }

  if (!items || items.length === 0) {
    return (
      <p style={{ color: "var(--text-dim)" }}>
        Nenhum item para exibir com os filtros atuais.
      </p>
    );
  }

  return (
    <div
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: 8,
        overflow: "auto",
        maxHeight: 520,
      }}
    >
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            {COLUMNS.map((col) => (
              <th
                key={col.key}
                onClick={() => handleSort(col.key)}
                style={{
                  ...cellStyle,
                  textAlign: "left",
                  color: "var(--text-dim)",
                  cursor: "pointer",
                  userSelect: "none",
                  position: "sticky",
                  top: 0,
                  background: "var(--surface)",
                  whiteSpace: "nowrap",
                }}
              >
                {col.label}
                {sortKey === col.key ? (sortDir === "asc" ? " ▲" : " ▼") : ""}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((item) => (
            <tr key={item.id ?? item.link}>
              <td style={cellStyle}>
                <a href={item.link} target="_blank" rel="noopener noreferrer">
                  {item.title}
                </a>
              </td>
              <td style={cellStyle}>{formatCurrency(item.price)}</td>
              <td style={cellStyle}>{formatInt(item.cpu_score)}</td>
              <td style={cellStyle}>{formatInt(item.gpu_score)}</td>
              <td style={cellStyle}>{formatInt(item.system_score)}</td>
              <td style={cellStyle}>
                {item.value_ratio != null ? formatDecimal(item.value_ratio, 2) : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
