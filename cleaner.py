import sqlite3
import time
import random
from curl_cffi import requests
from bs4 import BeautifulSoup
from config import DB_NAME


class Cleaner:
    def __init__(self, db_name=DB_NAME):
        self.db_name = db_name
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
        }

    def get_all_items(self):
        """Pega todos os IDs e Links do banco"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT id, link, title FROM OLX_ITENS_RAW")
        items = cursor.fetchall()
        conn.close()
        return items

    def check_link_status(self, url):
        """
        Retorna False se o link estiver inválido/vendido.
        Retorna True se estiver ativo.
        """
        try:
            # Usa impersonate para não ser bloqueado imediatamente (simula Chrome real)
            response = requests.get(url, impersonate="chrome110", timeout=15)

            # ---------------------------------------------------------
            # 1. Checagem de Código de Status HTTP
            # ---------------------------------------------------------
            if response.status_code == 404:
                return False, "Erro 404 (Not Found)"

            if response.status_code == 301 or response.status_code == 302:
                # Redirecionamentos na OLX geralmente levam para a Home ou Categorias
                return False, "Redirecionamento (Possível remoção)"

            # ---------------------------------------------------------
            # 2. Checagem de Estrutura Interna (DataLayer) - MAIS ROBUSTO
            # ---------------------------------------------------------
            # A OLX define o tipo de página num JSON interno.
            # Se for "page_not_found", o anúncio caiu, independente do texto na tela.
            if '"pageType":"page_not_found"' in response.text:
                return False, "Detectado via DataLayer (page_not_found)"

            # ---------------------------------------------------------
            # 3. Checagem de Conteúdo Visual (Soft 404)
            # ---------------------------------------------------------
            soup = BeautifulSoup(response.text, 'html.parser')
            text_content = soup.get_text().lower()

            # Obtém o título da página com segurança
            page_title = soup.title.string.lower() if soup.title else ""

            # Lista de frases que indicam que o anúncio não existe mais
            patterns_invalid = [
                "anúncio finalizado",
                "página não encontrada",
                "anúncio não encontrado",  # Adicionado para o seu caso específico
                "ops! não encontramos",
                "esse anúncio não está mais disponível",
                "vendido"
            ]

            # Se o título da página JÁ DIZ que não foi encontrado, não precisa de mais validação
            if "anúncio não encontrado" in page_title:
                return False, "Título indica: Anúncio não encontrado"

            for pattern in patterns_invalid:
                if pattern in text_content:
                    # Validação de segurança para evitar falsos positivos
                    # (Ex: Vendedor escreveu "não vendido separado" na descrição)

                    # Se encontrou o padrão, verificamos se o TÍTULO ou CABEÇALHO confirma o problema
                    keywords_confirmacao = [
                        "indisponível",
                        "erro",
                        "não encontrado",
                        "finalizado",
                        "ops!"
                    ]

                    if any(key in page_title for key in keywords_confirmacao):
                        return False, f"Detectado texto: '{pattern}'"

                    # Caso especial: "Anúncio finalizado" muitas vezes aparece em popups/alertas
                    if "anúncio finalizado" in pattern:
                        return False, "Anúncio Finalizado (Texto)"

            return True, "Ativo"

        except Exception as e:
            # Se der erro de conexão, assumimos que está temporariamente fora, NÃO deletamos
            print(f"   [AVISO] Erro de conexão ao verificar: {e}")
            return True, "Erro de Conexão (Mantido)"

    def delete_item(self, item_id):
        """Remove o item e suas specs do banco"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        try:
            # Remove das tabelas filhas primeiro (Specs)
            cursor.execute("DELETE FROM CPU_SPECS WHERE id_olxTable = ?", (item_id,))
            cursor.execute("DELETE FROM GPU_SPECS WHERE id_olxTable = ?", (item_id,))

            # Remove da tabela pai
            cursor.execute("DELETE FROM OLX_ITENS_RAW WHERE id = ?", (item_id,))

            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Erro ao deletar ID {item_id}: {e}")
            return False
        finally:
            conn.close()

    def run_cleaning_cycle(self):
        items = self.get_all_items()
        total = len(items)
        print(f"=== INICIANDO LIMPEZA: {total} itens para verificar ===")

        removed_count = 0

        for index, (item_id, link, title) in enumerate(items, 1):
            print(f"[{index}/{total}] Verificando ID {item_id}...", end=" ", flush=True)

            is_valid, reason = self.check_link_status(link)

            if not is_valid:
                print(f"❌ REMOVENDO ({reason})")
                self.delete_item(item_id)
                removed_count += 1
            else:
                print(f"✅ OK")

            # Pausa aleatória para evitar bloqueio de IP
            time.sleep(random.uniform(1.0, 2.5))

        print(f"\n=== LIMPEZA CONCLUÍDA ===")
        print(f"Total Removido: {removed_count}")
        print(f"Total Restante: {total - removed_count}")


if __name__ == "__main__":
    cleaner = Cleaner()
    cleaner.run_cleaning_cycle()
