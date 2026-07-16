"""
Validação e higienização dos dados raspados, no mesmo espírito do
schema/schemas.py do ImobData: em vez de confiar cegamente no que o regex
de specs.py extraiu, cada item passa por um modelo Pydantic que:

  1) Converte tipos (preço "R$ 1.200" -> 1200.0, "8GB" -> 8)
  2) Aplica valores-padrão sãos quando o campo vier vazio
  3) Barra itens fora do escopo do projeto (ex: sem preço, sem título)

Isso substitui checagens soltas espalhadas pelo código por um único lugar
de verdade sobre "o que é um item válido".
"""
import re
from typing import Optional, Any
from pydantic import BaseModel, field_validator, model_validator, ValidationError

__all__ = ["ItemPCSchema", "ValidationError"]


def limpar_moeda(valor) -> float:
    """Remove 'R$', pontos de milhar e espaços. Reaproveita a mesma ideia
    de schema/schemas.py do ImobData (limpar_moeda), adaptada ao formato
    de preço da OLX (já vem tratado por parse_price, mas fica resiliente
    caso receba string crua)."""
    if valor is None:
        return 0.0
    if isinstance(valor, (int, float)):
        return float(valor)
    texto = str(valor).replace("R$", "").replace(".", "").strip()
    texto = texto.replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return 0.0


def extrair_inteiro(valor) -> Optional[int]:
    """Extrai o primeiro número inteiro de uma string tipo '16 GB'. Retorna
    None (não 0) quando não há dado, para diferenciar 'não informado' de
    'zero', diferente do extrair_inteiro do ImobData onde 0 é aceitável."""
    if valor is None:
        return None
    if isinstance(valor, int):
        return valor
    texto = str(valor)
    if texto.strip().upper() in ("N/A", ""):
        return None
    busca = re.search(r"\d+", texto)
    return int(busca.group()) if busca else None


class ItemPCSchema(BaseModel):
    title: str
    price: float
    link: str
    cpu: str = "N/A"
    ram_gb: Optional[int] = None
    gpu: str = "N/A"
    storage: str = "N/A"
    city: str = "Não Informado"
    area: Optional[str] = None

    # 1. Filtro: barra itens sem preço ou sem link (dados inutilizáveis)
    @model_validator(mode="before")
    @classmethod
    def filtrar_itens_invalidos(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if not data.get("link"):
                raise ValueError("Ignorado: item sem link.")
            preco = limpar_moeda(data.get("price"))
            if preco <= 0:
                raise ValueError("Ignorado: item sem preço válido (possível troca/doação).")
        return data

    @field_validator("price", mode="before")
    @classmethod
    def validar_preco(cls, v):
        return limpar_moeda(v)

    @field_validator("ram_gb", mode="before")
    @classmethod
    def validar_ram(cls, v):
        return extrair_inteiro(v)

    @field_validator("city", mode="before")
    @classmethod
    def tratar_cidade_nula(cls, v):
        return v if v else "Não Informado"
