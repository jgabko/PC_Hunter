import re
import time
import random
import sys
from pathlib import Path
from bs4 import BeautifulSoup
from curl_cffi import requests
from curl_cffi.requests.exceptions import RequestsException
from pydantic import ValidationError

# Garante que a raiz do projeto esteja no sys.path, para que os imports
# absolutos abaixo (config, schema, persistence, processing) funcionem
# tanto rodando `python pipeline.py` quanto `python scraping/olx.py`
# diretamente ou `python -m scraping.olx`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Bibliotecas locais (agora organizadas em pacotes, como no ImobData)
from persistence import persist as Persist
from scraping import olx_detail_page
from processing.specs import parse_specs, parse_loc, parse_price
from schema.schema import ItemPCSchema
from config import BASE_URL

# Importa a pipeline híbrida
from processing.specs_AI import process_pipeline

# --- CONFIGURAÇÕES ---
START_PAGE = 1
PROCESS_AI_EVERY_X_PAGES = 1
AI_BATCH_SIZE = 5  # Reduzido para 5 para evitar erros de limite na Groq
MAX_ERROS_CONSECUTIVOS = 5  # Trava de segurança: para o scraper se a página falhar repetidamente

def get_random_sleep(min_s=2, max_s=5):
    """Dorme um tempo aleatório para parecer humano"""
    time.sleep(random.uniform(min_s, max_s))

def check_link_exists(link):
    """Verifica se o link já existe no banco."""
    conn = Persist.persist_init()  # abre conexão com o Postgres/Supabase
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM olx_itens_raw WHERE link = %s", (link,))
    exists = cursor.fetchone()
    conn.close()
    return exists is not None

def main():
    # Valida a conexão com o Postgres/Supabase ANTES de qualquer consulta
    # (falha rápido e com erro claro se DATABASE_URL estiver errada/faltando,
    # em vez de quebrar silenciosamente lá na frente). As tabelas em si já
    # devem existir — foram criadas uma vez via schema_postgres.sql.
    Persist.persist_init().close()

    page_number = START_PAGE
    max_page = False
    count_new = 0
    count_skipped = 0
    pages_processed = 0
    erros_consecutivos = 0

    print(f"=== INICIANDO SCRAPER NA PÁGINA {page_number} ===")

    while not max_page:
        if page_number == 0 :
            current_url=BASE_URL
        else:
            current_url = f"{BASE_URL}&o={page_number}"
        print(f'\n>>> Lendo Página {page_number}...')

        try:
            response = requests.get(current_url, impersonate="chrome110", timeout=30)
            if response.status_code != 200:
                erros_consecutivos += 1
                print(f"Erro {response.status_code}. Pausa de 30s... ({erros_consecutivos}/{MAX_ERROS_CONSECUTIVOS})")
                if erros_consecutivos >= MAX_ERROS_CONSECUTIVOS:
                    print("Muitos erros consecutivos. Encerrando para evitar loop infinito / bloqueio de IP.")
                    break
                time.sleep(30)
                continue
            erros_consecutivos = 0
        except RequestsException as e:
            print(f"Erro fatal na conexão: {e}")
            break

        soup = BeautifulSoup(response.text, 'html.parser')

        ad_count_div = soup.find('div', attrs={'id': 'total-of-ads'})
        if not ad_count_div:
            print("Layout desconhecido ou Captcha. Parando por segurança.")
            break

        if '0 de 0 resultados' in ad_count_div.text.strip():
            print("FIM DOS RESULTADOS.")
            max_page = True
            break

        main_content = soup.find('main', id='main-content')
        if not main_content:
            main_content = soup.find('div', attrs={'class': re.compile(r'AdListing_adListContainer.*')})

        if main_content:
            ad_list = main_content.find_all('section', attrs={'class': 'olx-adcard'})

            if not ad_list:
                print("Nenhum anúncio encontrado nesta página.")

            for ads in ad_list:
                try:
                    link_tag = ads.find('a')
                    if not link_tag: continue
                    link = link_tag.get('href')

                    h2 = ads.find('h2')
                    title = h2.text.strip() if h2 else "Sem Título"

                    # Se já existe, pula
                    if check_link_exists(link):
                        print(f"  [PULADO] Já existe: {title[:30]}...")
                        count_skipped += 1
                        continue

                    # Se é novo, processa
                    get_random_sleep(1.5, 3.0)
                    details = olx_detail_page.getDetails(link)

                    price_tag = ads.find('h3', attrs={'class': re.compile(r'olx-adcard__price')})
                    price = price_tag.text.strip() if price_tag else "0"

                    loc_tag = ads.find('p', attrs={'class': re.compile(r'olx-adcard__location')})
                    local_text = loc_tag.text.strip() if loc_tag else ""

                    specs = parse_specs(title, details)
                    local_dict = parse_loc(local_text)
                    price_final = parse_price(price)

                    # Validação/higienização (mesmo espírito do schema/schemas.py
                    # do ImobData): barra itens sem preço ou link antes de gravar.
                    try:
                        ItemPCSchema.model_validate({
                            "title": title,
                            "price": price_final,
                            "link": link,
                            "cpu": specs.get("cpu"),
                            "ram_gb": specs.get("ram"),
                            "gpu": specs.get("gpu"),
                            "storage": specs.get("storage"),
                            "city": local_dict.get("cidade"),
                            "area": local_dict.get("bairro"),
                        })
                    except ValidationError as validacao_erro:
                        msg_erro = str(validacao_erro).split("\n")[0]
                        print(f"  [IGNORADO] Filtro: {msg_erro[:80]}")
                        continue

                    Persist.persist(title, price_final, link, specs, local_dict, details)
                    count_new += 1
                    print(f"  [NOVO] Item salvo: {title[:40]}... (R$ {price_final})")

                except Exception as e_item:
                    print(f"  [ERRO] Item falhou: {e_item}")
                    continue

        print(f"--- Fim Pág {page_number}: {count_new} Novos / {count_skipped} Pulados ---")

        page_number += 1
        pages_processed += 1

        # GATILHO DA IA
        if pages_processed % PROCESS_AI_EVERY_X_PAGES == 0:
            print("\n>>> INICIANDO PROCESSAMENTO INTELIGENTE (REGEX + IA)...")
            try:
                pending_rows = Persist.search_pending_items()
                if pending_rows:
                    process_pipeline(pending_rows, batch_size=AI_BATCH_SIZE)
                else:
                    print(">>> Nenhum item pendente para processar.")
            except Exception as e_ai:
                print(f"Erro na Pipeline IA: {e_ai}")
            print(">>> Retornando ao Scraping...\n")

        get_random_sleep(3, 5)

if __name__ == "__main__":
    main()
