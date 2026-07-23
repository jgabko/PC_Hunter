import { useEffect, useState } from "react";
import { api } from "../api";
import FlipCard from "./FlipCard";

export default function FlipsList({ filters, refreshKey }) {
  const [items, setItems] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    setError(null);
    api
      .getFlips(filters)
      .then((data) => setItems(data.items))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [filters, refreshKey]);

  if (loading && !items) {
    return <p style={{ color: "var(--text-dim)" }}>Carregando oportunidades...</p>;
  }

  if (error) {
    return (
      <p style={{ color: "var(--danger)" }}>
        Erro ao carregar oportunidades de upgrade: {error}
      </p>
    );
  }

  if (!items || items.length === 0) {
    return (
      <p style={{ color: "var(--text-dim)" }}>
        Nenhuma oportunidade de upgrade lucrativa encontrada com os filtros
        atuais.
      </p>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      {items.map((item) => (
        <FlipCard key={item.id ?? item.link} item={item} />
      ))}
    </div>
  );
}
