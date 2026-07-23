import psycopg2
import pandas as pd
import numpy as np
from benchmarks import BenchmarkLoader
from config import DATABASE_URL


class PCRanking:
    def __init__(self):
        self.bench = BenchmarkLoader()
        self.conn = psycopg2.connect(DATABASE_URL)

        # --- CONFIGURAÇÕES DE REALIDADE FINANCEIRA ---
        self.current_market_rate = 0.18  # Valor base (será ajustado dinamicamente)
        self.NEGOTIATION_MARGIN = 0.15  # 15% de desconto que você dará na venda
        self.OPERATIONAL_COST = 50.00  # Custo fixo (Gasolina/Uber + Pasta Térmica)

    def load_data(self):
        """Carrega dados brutos do banco"""
        query = """
        SELECT id, title, price, link, cpu, gpu, ram, storage
        FROM olx_itens_raw
        WHERE ai_check = 1 AND price > 0
        """
        df = pd.read_sql_query(query, self.conn)
        return df

    def detect_office_pc(self, title):
        """Identifica PCs corporativos que precisam de gabinete novo"""
        office_keywords = ['dell', 'optiplex', 'hp', 'lenovo', 'thinkcentre', 'prodesk', 'elitedesk', 'compaq']
        t = str(title).lower()
        return any(k in t for k in office_keywords)

    def analyze_market(self):
        """Calcula scores, limpa erros e define a taxa de mercado"""
        df = self.load_data()

        if df.empty: return df

        print(">>> Calculando pontuações e aplicando travas de segurança...")

        # 1. Pontuações Individuais
        df['cpu_score'] = df['cpu'].apply(lambda x: self.bench.get_score(x, 'cpu'))
        df['gpu_score'] = df['gpu'].apply(lambda x: self.bench.get_score(x, 'gpu'))
        df['ram_score'] = df['ram'].apply(self.bench.get_ram_score)
        df['storage_score'] = df['storage'].apply(self.bench.get_storage_score)

        # --- TRAVA DE SANIDADE (CORREÇÃO DO BUG DO TELEFONE) ---
        # Se a RAM valer mais que 25.600 pontos (128GB), é erro de leitura (número de telefone). Zera.
        df.loc[df['ram_score'] > 25600, 'ram_score'] = 0

        # Se o score total for absurdo (> 100k), zera.
        df['system_score'] = df['cpu_score'] + df['gpu_score'] + df['ram_score'] + df['storage_score']
        df.loc[df['system_score'] > 100000, 'system_score'] = 0

        # 2. Identificação de Office
        df['is_office'] = df['title'].apply(self.detect_office_pc)

        # 3. Ratio (Custo-Benefício)
        df['value_ratio'] = df.apply(lambda row: row['system_score'] / row['price'] if row['price'] > 0 else 0, axis=1)

        # 4. Taxa de Mercado Dinâmica (Dynamic Pricing) with HARD CAP
        # Filtra sucatas e erros para a média
        valid_market = df[(df['system_score'] > 3000) & (df['price'] > 300)]

        if not valid_market.empty:
            median_ratio = valid_market['value_ratio'].median()

            if median_ratio > 0:
                raw_rate = 1 / median_ratio
                # TRAVA DE MERCADO: Ninguém paga mais que R$ 0.22 por ponto em usado
                self.current_market_rate = min(raw_rate, 0.22)
            else:
                self.current_market_rate = 0.18
        else:
            self.current_market_rate = 0.18

        return df

    def find_flip_opportunities(self, df):
        """Encontra oportunidades de upgrade simples"""
        opportunities = []

        for index, row in df.iterrows():
            # Ignora itens com score zerado por erro
            if row['system_score'] == 0: continue

            cpu_s = row['cpu_score']
            gpu_s = row['gpu_score']
            price = row['price']

            # Custo extra se for Dell/HP
            reshell_cost = 180 if row['is_office'] else 0

            # CENÁRIO 1: FALTA GPU (Upgrade)
            # CPU Forte (>8000) e GPU Fraca (<3000)
            if cpu_s > 8000 and gpu_s < 3000:
                potential_upgrade = "Add GPU (RTX 2060)"
                gpu_cost = 1200  # Custo peça usada

                # Custo Total = Preço + Peça + Gabinete(se precisar) + Operacional
                total_proj_cost = price + gpu_cost + reshell_cost + self.OPERATIONAL_COST

                # Novo Score (+14k da RTX)
                new_total_score = row['system_score'] + 14000

                # Venda Realista (Score * Rate * 0.85 para margem de negociação)
                raw_sell_price = new_total_score * self.current_market_rate
                est_sell_price = raw_sell_price * (1 - self.NEGOTIATION_MARGIN)

                profit = est_sell_price - total_proj_cost

                if profit > 400:  # Filtro de lucro mínimo
                    opportunities.append({
                        'id': row['id'],
                        'title': row['title'],
                        'current_price': price,
                        'type': 'FALTA_GPU',
                        'is_office': row['is_office'],
                        'strategy': potential_upgrade if not row['is_office'] else potential_upgrade + " + Case Novo",
                        'projected_cost': total_proj_cost,
                        'projected_score': new_total_score,
                        'est_sell': est_sell_price,
                        'est_profit': profit
                    })

            # CENÁRIO 2: ACHADO (Preço Errado)
            market_avg_ratio = 1 / self.current_market_rate
            # Se tiver 60% mais performance por real que a média
            if row['value_ratio'] > (market_avg_ratio * 1.6):

                clean_cost = 50 + reshell_cost + self.OPERATIONAL_COST
                total_proj_cost = price + clean_cost

                raw_sell_price = row['system_score'] * self.current_market_rate
                est_sell_price = raw_sell_price * (1 - self.NEGOTIATION_MARGIN)

                profit = est_sell_price - total_proj_cost

                if profit > 400:
                    opportunities.append({
                        'id': row['id'],
                        'title': row['title'],
                        'current_price': price,
                        'type': 'ACHADO_BARATO',
                        'is_office': row['is_office'],
                        'strategy': 'Revenda Rápida' if not row['is_office'] else 'Re-shell + Revenda',
                        'projected_cost': total_proj_cost,
                        'projected_score': row['system_score'],
                        'est_sell': est_sell_price,
                        'est_profit': profit
                    })

        return pd.DataFrame(opportunities).sort_values(by='est_profit', ascending=False).head(20)


if __name__ == "__main__":
    analyzer = PCRanking()
    df_analyzed = analyzer.analyze_market()
    if not df_analyzed.empty:
        print(f"Taxa de Mercado Hoje: {analyzer.current_market_rate:.4f}")