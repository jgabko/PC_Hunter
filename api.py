"""
API do PC Hunter - substitui o dashboard.py (Streamlit) por endpoints HTTP
que um frontend próprio (React/Vite) vai consumir.

Rodar com:
    uvicorn api:app --reload --port 8000

Docs interativas em:
    http://localhost:8000/docs
"""

import json

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from config import FRONTEND_ORIGINS

app = FastAPI(title="PC Hunter API")

# --- CORS ---
# Em dev, FRONTEND_ORIGINS cai no padrão do Vite (localhost:5173). Em
# produção, defina FRONTEND_ORIGINS no ambiente do Render com o domínio
# real do frontend (ex: https://pc-hunter.vercel.app) — ver .env.example.
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    """
    Verifica se a API está de pé e se consegue importar/instanciar
    o PCRanking (ou seja, se o banco de dados e o benchmarks.py
    estão acessíveis).
    """
    try:
        from flipper import PCRanking

        analyzer = PCRanking()
        analyzer.conn.close()
        return {"status": "ok", "pc_ranking": "ok"}
    except Exception as e:
        return {"status": "ok", "pc_ranking": "error", "detail": str(e)}


@app.get("/market")
def get_market(
    min_score: int = Query(3000, ge=0, description="Score mínimo do sistema"),
    min_price: float = Query(200, ge=0, description="Preço mínimo (R$)"),
    max_price: float = Query(4000, ge=0, description="Preço máximo (R$)"),
):
    """
    Substitui os sliders do sidebar do Streamlit.

    Roda analyze_market() (calcula scores, taxa de mercado dinâmica etc.)
    e devolve os itens já filtrados por score/preço, junto com a taxa de
    mercado e as métricas de cabeçalho (itens filtrados, preço médio).
    """
    from flipper import PCRanking

    analyzer = PCRanking()
    df = analyzer.analyze_market()
    analyzer.conn.close()

    if df.empty:
        return {
            "rate": 0.18,
            "count": 0,
            "avg_price": None,
            "items": [],
        }

    df_filtered = df[
        (df["system_score"] >= min_score)
        & (df["price"] >= min_price)
        & (df["price"] <= max_price)
    ].copy()

    # to_json lida bem com tipos numpy (int64/float64) e com NaN -> null,
    # diferente de to_dict() puro, que quebraria a serialização do FastAPI.
    items = json.loads(df_filtered.to_json(orient="records"))

    avg_price = (
        float(df_filtered["price"].mean()) if not df_filtered.empty else None
    )

    return {
        "rate": analyzer.current_market_rate,
        "count": len(df_filtered),
        "avg_price": avg_price,
        "items": items,
    }


@app.get("/flips")
def get_flips(
    min_score: int = Query(3000, ge=0, description="Score mínimo do sistema"),
    min_price: float = Query(200, ge=0, description="Preço mínimo (R$)"),
    max_price: float = Query(4000, ge=0, description="Preço máximo (R$)"),
):
    """
    Oportunidades de upgrade simples (aba "Upgrades" do dashboard antigo).

    Usa os mesmos filtros de score/preço do /market e roda
    find_flip_opportunities em cima do recorte filtrado.
    """
    from flipper import PCRanking

    analyzer = PCRanking()
    df = analyzer.analyze_market()

    if df.empty:
        analyzer.conn.close()
        return {"items": []}

    df_filtered = df[
        (df["system_score"] >= min_score)
        & (df["price"] >= min_price)
        & (df["price"] <= max_price)
    ].copy()

    flips = analyzer.find_flip_opportunities(df_filtered)
    analyzer.conn.close()

    if flips.empty:
        return {"items": []}

    # find_flip_opportunities não devolve o link do anúncio, então
    # trazemos de volta cruzando pelo id (igual o dashboard fazia).
    flips = flips.merge(df[["id", "link"]], on="id", how="left")

    items = json.loads(flips.to_json(orient="records"))
    return {"items": items}


def find_fusion_opportunities(df_bases, df_market, market_rate_now, min_price_filter):
    """
    Encontra combinações (Base + Doador) com custos e lucros realistas.

    Migrado de dashboard.py sem alterar a lógica de negócio — só trocamos
    o "container" (Streamlit -> função pura chamada pelo endpoint /fusions).
    """
    import pandas as pd

    matches = []

    # Constantes de Realidade
    NEGOTIATION_MARGIN = 0.15  # 15% de desconto na venda
    OPERATIONAL_COST = 50.00  # Custo fixo (deslocamento/pasta térmica)

    # Blacklist de sucata/notebooks
    blacklist = [
        "notebook", "laptop", "defeito", "quebrado", "tela", "samsung",
        "dell g15", "acer nitro", "sucata", "peças", "macbook", "all in one",
    ]

    def is_safe(title):
        return not any(bad in str(title).lower() for bad in blacklist)

    # Filtra doadores: seguros e acima do preço mínimo (evita anúncios de valor simbólico)
    valid_market = df_market[
        (df_market["title"].apply(is_safe)) & (df_market["price"] >= min_price_filter)
    ].copy()

    # Doadores: GPU decente (>4000) e baratos (<2000)
    potential_donors = valid_market[
        (valid_market["gpu_score"] > 4000) & (valid_market["price"] < 2000)
    ].sort_values(by="value_ratio", ascending=False).head(40)

    if potential_donors.empty or df_bases.empty:
        return pd.DataFrame()

    # Bases: já vêm filtradas pelo endpoint, mas garantimos segurança
    clean_bases = df_bases[df_bases["title"].apply(is_safe)].head(40)

    for idx_base, base in clean_bases.iterrows():
        if base["price"] > 3000:
            continue  # Base muito cara compromete o lucro

        for idx_donor, donor in potential_donors.iterrows():
            if base["id"] == donor["id"]:
                continue
            if base["gpu_score"] >= donor["gpu_score"]:
                continue  # Base já é melhor que o doador

            # --- SCORE PROJETADO (SOMA) ---
            projected_score = (
                base.get("cpu_score", 0)
                + donor.get("gpu_score", 0)
                + base.get("ram_score", 0)
                + base.get("storage_score", 0)
            )

            # --- CUSTOS EXTRAS ---
            extras_log = []
            custo_extra = OPERATIONAL_COST  # Começa com R$ 50

            # Fonte necessária?
            if donor.get("gpu_score", 0) > 8000:
                custo_extra += 250
                extras_log.append("Fonte 500W")

            # Gabinete necessário?
            if base.get("is_office", False):
                custo_extra += 180
                extras_log.append("Gabinete gamer")

            total_cost = base["price"] + donor["price"] + custo_extra

            # --- RECEITA ESTIMADA ---
            real_sell_value = (projected_score * market_rate_now) * (1 - NEGOTIATION_MARGIN)
            scrap_value = (donor["price"] * 0.35) + 80
            potential_profit = (real_sell_value + scrap_value) - total_cost

            if potential_profit > 400:  # Filtro de lucro mínimo
                matches.append({
                    "Base_Title": base["title"], "Base_Price": base["price"], "Base_Link": base["link"],
                    "Base_Is_Office": base.get("is_office", False),
                    "Donor_Title": donor["title"], "Donor_Price": donor["price"], "Donor_GPU": donor["gpu"],
                    "Donor_Link": donor["link"],
                    "Total_Cost": total_cost, "Extra_Details": ", ".join(extras_log) if extras_log else "Básico",
                    "Projected_Score": int(projected_score),
                    "Real_Sell_Value": real_sell_value,
                    "Est_Profit": potential_profit,
                })

    return pd.DataFrame(matches).sort_values(by="Est_Profit", ascending=False).head(20)


@app.get("/fusions")
def get_fusions(
    min_score: int = Query(3000, ge=0, description="Score mínimo do sistema"),
    min_price: float = Query(200, ge=0, description="Preço mínimo (R$)"),
    max_price: float = Query(4000, ge=0, description="Preço máximo (R$)"),
):
    """
    Oportunidades de combinação Base + Doador (aba "Combinações de
    Componentes" do dashboard antigo).
    """
    from flipper import PCRanking

    analyzer = PCRanking()
    df = analyzer.analyze_market()

    if df.empty:
        analyzer.conn.close()
        return {"items": []}

    df_filtered = df[
        (df["system_score"] >= min_score)
        & (df["price"] >= min_price)
        & (df["price"] <= max_price)
    ].copy()

    # Bases precisam ter CPU boa (>6000), igual ao dashboard antigo
    bases = df_filtered[df_filtered["cpu_score"] > 6000].copy()

    merges = find_fusion_opportunities(bases, df, analyzer.current_market_rate, min_price)
    analyzer.conn.close()

    if merges.empty:
        return {"items": []}

    items = json.loads(merges.to_json(orient="records"))
    return {"items": items}