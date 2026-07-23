import { useEffect, useState } from "react";
import { api } from "../api";
import FusionCard from "./FusionCard";

export default function FusionsList({ filters, refreshKey }) {
  const [items, setItems] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    setError(null);
    api
      .getFusions(filters)
      .then((data) => setItems(data.items))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [filters, refreshKey]);

  if (loading && !items) {
    return <p style={{ color: "var(--text-dim)" }}>Buscando combinações...</p>;
  }

  if (error) {
    return (
      <p style={{ color: "var(--danger)" }}>
        Erro ao carregar combinações: {error}
      </p>
    );
  }

  if (!items || items.length === 0) {
    return (
      <p style={{ color: "var(--text-dim)" }}>
        Nenhuma combinação Base + Doador lucrativa encontrada com os filtros
        atuais.
      </p>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      {items.map((item, idx) => (
        <FusionCard key={`${item.Base_Link}-${item.Donor_Link}-${idx}`} item={item} />
      ))}
    </div>
  );
}
