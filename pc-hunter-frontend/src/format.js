// Formata números no padrão brasileiro: milhar com ponto, decimal com vírgula.

export function formatCurrency(value) {
  if (value == null || Number.isNaN(value)) return "—";
  return `R$ ${Number(value).toLocaleString("pt-BR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

// Para inteiros (scores) - sem casas decimais, só separador de milhar.
export function formatInt(value) {
  if (value == null || Number.isNaN(value)) return "—";
  return Number(value).toLocaleString("pt-BR", {
    maximumFractionDigits: 0,
  });
}

// Para números com casas decimais (ex: custo-benefício, taxa de mercado).
export function formatDecimal(value, digits = 2) {
  if (value == null || Number.isNaN(value)) return "—";
  return Number(value).toLocaleString("pt-BR", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}
