import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="OLX PC Hunter",
    page_icon=None,
    layout="wide"
)

try:
    from flipper import PCRanking
except ImportError as e:
    st.error(
        f"ERRO ao importar flipper.py: {e}\n\n"
        "Se o erro acima mencionar um módulo (ex: 'No module named ...'), "
        "rode: pip install -r requirements.txt"
    )
    st.stop()

# ==============================================================================
# ESTILO (tons de azul e preto sobre o tema nativo do Streamlit)
# ==============================================================================
# A paleta principal fica em .streamlit/config.toml (tema nativo: fundo preto,
# destaque azul). O bloco abaixo só ajusta detalhes que o tema não cobre
# (bordas de expander, cor de foco dos sliders, hover dos botões).

st.markdown(
    """
<style>
:root {
    --accent-blue: #4C8DFF;
    --accent-blue-dim: #2451A3;
    --surface: #12161F;
    --border: #232937;
}

/* Expanders (cards de oportunidade) */
[data-testid="stExpander"] {
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent-blue-dim);
    border-radius: 8px;
    background-color: var(--surface);
}
[data-testid="stExpander"] summary {
    font-weight: 500;
}

/* Métricas */
[data-testid="stMetric"] {
    background-color: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px 16px;
}
[data-testid="stMetricValue"] {
    color: var(--accent-blue);
}

/* Botões */
.stButton button {
    border: 1px solid var(--border);
    color: var(--accent-blue);
}
.stButton button:hover {
    border-color: var(--accent-blue);
    color: var(--accent-blue);
}

/* Abas */
[data-baseweb="tab-highlight"] {
    background-color: var(--accent-blue) !important;
}
[aria-selected="true"] {
    color: var(--accent-blue) !important;
}

/* Sliders */
[data-testid="stSlider"] [role="slider"] {
    background-color: var(--accent-blue);
    border-color: var(--accent-blue);
}

/* Tabela */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
}

/* Caixas de aviso/erro/info (st.warning, st.error, st.info, st.success) —
   removido vermelho/laranja/verde padrão, tudo neutro em azul agora */
[data-testid="stAlert"] {
    background-color: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-left: 3px solid var(--accent-blue) !important;
}
[data-testid="stAlert"] * {
    color: var(--text-color, #E8EAF0) !important;
}
[data-testid="stAlert"] svg {
    fill: var(--accent-blue) !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# ==============================================================================
# LÓGICA DE FUSÃO (BASE + DOADOR) - REALISTA
# ==============================================================================
def find_fusion_opportunities(df_bases, df_market, market_rate_now, min_price_filter):
    """
    Encontra combinações (Base + Doador) com custos e lucros realistas.
    """
    matches = []

    # Constantes de Realidade
    NEGOTIATION_MARGIN = 0.15  # 15% de desconto na venda
    OPERATIONAL_COST = 50.00  # Custo fixo (deslocamento/pasta térmica)

    # Blacklist de sucata/notebooks
    blacklist = ['notebook', 'laptop', 'defeito', 'quebrado', 'tela', 'samsung', 'dell g15', 'acer nitro', 'sucata',
                 'peças', 'macbook', 'all in one']

    def is_safe(title):
        return not any(bad in str(title).lower() for bad in blacklist)

    # Filtra doadores: seguros e acima do preço mínimo (evita anúncios de valor simbólico)
    valid_market = df_market[
        (df_market['title'].apply(is_safe)) &
        (df_market['price'] >= min_price_filter)
        ].copy()

    # Doadores: GPU decente (>4000) e baratos (<2000)
    potential_donors = valid_market[
        (valid_market['gpu_score'] > 4000) &
        (valid_market['price'] < 2000)
        ].sort_values(by='value_ratio', ascending=False).head(40)

    if potential_donors.empty or df_bases.empty: return pd.DataFrame()

    # Bases: já vêm filtradas pelo dashboard, mas garantimos segurança
    clean_bases = df_bases[df_bases['title'].apply(is_safe)].head(40)

    for idx_base, base in clean_bases.iterrows():
        if base['price'] > 3000: continue  # Base muito cara compromete o lucro
        for idx_donor, donor in potential_donors.iterrows():
            if base['id'] == donor['id']: continue
            if base['gpu_score'] >= donor['gpu_score']: continue  # Base já é melhor que o doador

            # --- SCORE PROJETADO (SOMA) ---
            # Soma CPU Base + GPU Doador + RAM Base + Storage Base
            projected_score = (
                    base.get('cpu_score', 0) +
                    donor.get('gpu_score', 0) +
                    base.get('ram_score', 0) +
                    base.get('storage_score', 0)
            )

            # --- CUSTOS EXTRAS ---
            extras_log = []
            custo_extra = OPERATIONAL_COST  # Começa com R$ 50

            # Fonte necessária?
            if donor.get('gpu_score', 0) > 8000:
                custo_extra += 250;
                extras_log.append("Fonte 500W")

            # Gabinete necessário?
            if base.get('is_office', False):
                custo_extra += 180;
                extras_log.append("Gabinete gamer")

            total_cost = base['price'] + donor['price'] + custo_extra

            # --- RECEITA ESTIMADA ---
            # Venda do PC principal (com desconto de negociação)
            real_sell_value = (projected_score * market_rate_now) * (1 - NEGOTIATION_MARGIN)

            # Venda dos componentes remanescentes do doador + GPU antiga da base
            # Estimativa conservadora: 35% do valor do doador + R$ 80 da GPU antiga
            scrap_value = (donor['price'] * 0.35) + 80

            potential_profit = (real_sell_value + scrap_value) - total_cost

            if potential_profit > 400:  # Filtro de lucro mínimo
                matches.append({
                    'Base_Title': base['title'], 'Base_Price': base['price'], 'Base_Link': base['link'],
                    'Base_Is_Office': base.get('is_office', False),
                    'Donor_Title': donor['title'], 'Donor_Price': donor['price'], 'Donor_GPU': donor['gpu'],
                    'Donor_Link': donor['link'],
                    'Total_Cost': total_cost, 'Extra_Details': ", ".join(extras_log) if extras_log else "Básico",
                    'Projected_Score': int(projected_score),
                    'Real_Sell_Value': real_sell_value,
                    'Est_Profit': potential_profit
                })

    return pd.DataFrame(matches).sort_values(by='Est_Profit', ascending=False).head(20)


# ==============================================================================
# CARREGAMENTO E SIDEBAR
# ==============================================================================
@st.cache_data
def get_market_analysis():
    try:
        temp = PCRanking()
        df = temp.analyze_market()
        rate = temp.current_market_rate
        temp.conn.close()
        return df, rate
    except:
        return pd.DataFrame(), 0.18


st.title("OLX PC Hunter")
st.caption("Margens aplicadas: -15% na venda (negociação) | +R$ 50 de custo operacional (deslocamento/pasta térmica)")

if st.sidebar.button("Recarregar"): st.cache_data.clear(); st.rerun()

df, rate = get_market_analysis()
if df.empty: st.warning("Banco de dados vazio. Rode o 'olx.py'."); st.stop()

# Sincroniza taxa
analyzer = PCRanking()
analyzer.current_market_rate = rate

# Sliders de Filtro
min_score = st.sidebar.slider("Score Mínimo", 0, 50000, 3000, 500)
min_price = st.sidebar.slider("Preço Mínimo (R$)", 0, 5000, 200, 50)  # Padrão 200 para evitar cabos/jogos
max_price = st.sidebar.slider("Preço Máximo (R$)", 100, 10000, 4000, 100)

df_filtered = df[
    (df['system_score'] >= min_score) &
    (df['price'] >= min_price) &
    (df['price'] <= max_price)
    ].copy()

# Métricas do cabeçalho
c1, c2, c3 = st.columns(3)
c1.metric("Itens Filtrados", len(df_filtered))
c2.metric("Taxa de Mercado (Dinâmica)", f"R$ {rate:.3f}/pt")
c3.metric("Preço Médio", f"R$ {df_filtered['price'].mean():.0f}")

# ==============================================================================
# ABAS
# ==============================================================================
tab1, tab2, tab3 = st.tabs(["Upgrades", "Combinações de Componentes", "Dados"])

with tab1:
    st.subheader("Oportunidades de Upgrade Simples")
    if not df_filtered.empty:
        flips = analyzer.find_flip_opportunities(df_filtered)  # Retorna TOP 20 filtrado
        if not flips.empty:
            for _, row in flips.iterrows():
                with st.expander(f"Lucro Líquido: R$ {row['est_profit']:.2f} | {row['title']}"):
                    col1, col2, col3 = st.columns(3)
                    col1.write(f"Compra: **R$ {row['current_price']:.0f}**")
                    col1.caption(f"Custo Projeto: R$ {row['projected_cost']:.0f}")
                    col2.write(f"Venda (já com desconto): **R$ {row['est_sell']:.0f}**")
                    col2.caption(f"Score: {int(row['projected_score'])}")
                    col3.info(row['strategy'])
                    if not df[df['id'] == row['id']].empty:
                        col3.markdown(f"[Ver anúncio]({df[df['id'] == row['id']].iloc[0]['link']})")
        else:
            st.info("Nenhum upgrade com lucro acima de R$ 400 encontrado.")

with tab2:
    st.subheader("Oportunidades de Combinação (Base + Doador)")
    if not df_filtered.empty:
        # Bases precisam ter CPU boa (>6000)
        bases = df_filtered[df_filtered['cpu_score'] > 6000].copy()

        with st.spinner("Analisando combinações..."):
            merges = find_fusion_opportunities(bases, df, rate, min_price)

        if not merges.empty:
            for _, row in merges.iterrows():
                with st.expander(f"Lucro Líquido: R$ {row['Est_Profit']:.2f} | Score: {row['Projected_Score']}"):
                    c1, c2, c3 = st.columns(3)

                    # Coluna Base
                    c1.markdown("**Base**")
                    c1.caption(f"{row['Base_Title'][:25]}...")
                    if row['Base_Is_Office']: c1.warning("Configuração de escritório (requer gabinete novo)")
                    c1.write(f"R$ {row['Base_Price']:.0f}")
                    c1.markdown(f"[Ver anúncio]({row['Base_Link']})")

                    # Coluna Doador
                    c2.markdown("**Doador**")
                    c2.caption(f"{row['Donor_Title'][:25]}...")
                    c2.markdown(f"**{row['Donor_GPU']}**")
                    c2.write(f"R$ {row['Donor_Price']:.0f}")
                    c2.markdown(f"[Ver anúncio]({row['Donor_Link']})")

                    # Coluna Financeira
                    c3.markdown("**Resultado**")
                    c3.write(f"Custo Total: **R$ {row['Total_Cost']:.0f}**")
                    c3.write(f"Venda Estimada: **R$ {row['Real_Sell_Value']:.0f}**")
                    c3.caption(f"Extras: {row['Extra_Details']} + R$ 50 de operação")
        else:
            st.info("Nenhuma combinação lucrativa encontrada.")

with tab3:
    st.dataframe(
        df_filtered[['title', 'price', 'system_score', 'value_ratio', 'link']].sort_values('value_ratio',
                                                                                           ascending=False),
        hide_index=True,
        use_container_width=True,
        column_config={"link": st.column_config.LinkColumn("Link")}
    )
