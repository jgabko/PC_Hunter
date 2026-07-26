"""
Camada de persistência (Postgres/Supabase) do scraper de PCs da OLX.

Migrado de SQLite para Postgres (Etapa 1 da migração para nuvem). As
tabelas em si NÃO são mais criadas por este módulo: rode
`schema_postgres.sql` uma vez no SQL Editor do Supabase antes de usar.

Tabelas (nomes em minúsculo, convenção do Postgres):

  olx_itens_raw
    id (pk), title, price, link (unique), cpu, ram, ram_tech, gpu, storage,
    storage_type, city, area, details, date_publish,
    latest (1 = versão mais recente do anúncio; 0 = versão antiga arquivada
            quando o mesmo link reaparece com dados diferentes),
    ai_check (0 = specs ainda não passaram pelo pipeline regex/IA; 1 = já passou)

  cpu_specs / gpu_specs
    tabelas filhas (fk id_olxtable -> olx_itens_raw.id) com as specs
    detalhadas extraídas pelo pipeline híbrido (regex + IA) em specs_AI.py.

NOTA IMPORTANTE (bug pré-existente, preservado no port 1:1 desta etapa):
o link tem constraint UNIQUE. O fluxo de "arquivar versão antiga" faz um
UPDATE pondo latest=0 na linha existente e tenta inserir uma nova linha
com o MESMO link — isso viola a UNIQUE e o INSERT é ignorado (igual o
"INSERT OR IGNORE" fazia no SQLite). Ou seja, hoje um anúncio que reaparece
com dados diferentes fica com latest=0 e nunca ganha uma linha latest=1
nova. Não mudei esse comportamento aqui para manter a Etapa 1 focada só
em troca de banco — mas vale corrigir numa etapa futura (ex: permitir
múltiplas linhas por link, ou fazer UPSERT de verdade).
"""
import sys
from pathlib import Path
from contextlib import contextmanager

import psycopg2
import psycopg2.extras
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import DATABASE_URL


# --- CONEXÃO ---

def get_connection():
    """Abre uma conexão nova com o Postgres (Supabase)."""
    return psycopg2.connect(DATABASE_URL)


def persist_init():
    """
    Mantido por compatibilidade com quem já importava persist_init()
    esperando uma conexão pronta pra usar. Diferente da versão SQLite,
    NÃO cria mais as tabelas (isso agora é feito uma vez via
    schema_postgres.sql) — só abre e devolve a conexão.
    """
    return get_connection()


# --- FUNÇÕES DE INSERÇÃO RAW (SCRAPING) ---

def persist(title, price, link, specs, local, details):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        persist_item(conn, cursor, title, price, link, specs, local, details)
    finally:
        conn.close()


def _sem_nul(valor):
    """
    Remove bytes NUL (\\x00) de strings antes de mandar pro Postgres.
    O Postgres recusa qualquer texto com esse caractere (erro "A string
    literal cannot contain NUL (0x00) characters"), e de vez em quando
    aparece um anúncio da OLX com isso na descrição (geralmente texto
    colado de Word/PDF). Sem isso, o item inteiro falha silenciosamente.
    """
    if isinstance(valor, str):
        return valor.replace("\x00", "")
    return valor


def persist_item(conn, cursor, title, price, link, specs, local, details):
    gpu = _sem_nul(specs.get('gpu'))
    ram = _sem_nul(specs.get('ram'))
    cpu = _sem_nul(specs.get('cpu'))
    storage = _sem_nul(specs.get('storage'))
    city = _sem_nul(local.get('cidade'))
    area = _sem_nul(local.get('bairro'))
    description = _sem_nul(details.get('Descrição'))
    title = _sem_nul(title)

    existence = check_exits(conn, link)

    try:
        if existence:
            # Arquiva o anúncio antigo (latest=0). Ver nota no topo do
            # arquivo sobre a limitação da UNIQUE em link.
            cursor.execute(
                "UPDATE olx_itens_raw SET latest=0 WHERE link=%s AND latest=1;",
                (link,),
            )

        cursor.execute(
            """
            INSERT INTO olx_itens_raw
            (title, price, link, cpu, ram, gpu, storage, city, area, details, date_publish, latest, ai_check)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, NOW(), 1, 0)
            ON CONFLICT (link) DO NOTHING
            """,
            (title, price, link, cpu, ram, gpu, storage, city, area, description),
        )

        conn.commit()
    except psycopg2.Error as e:
        conn.rollback()
        print(f"Erro SQL ao persistir item: {e}")


def check_exits(conn, link):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM olx_itens_raw WHERE link=%s;", (link,))
    return cursor.fetchall()


def search_pending_items():
    conn = get_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT id, title, details FROM olx_itens_raw WHERE ai_check = 0")
        rows = cursor.fetchall()
    finally:
        conn.close()
    return rows


def persist_view():
    conn = get_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM olx_itens_raw ORDER BY id DESC LIMIT 5", conn)
        print(df)
    except Exception:
        print("Banco vazio ou erro de leitura.")
    finally:
        conn.close()


# --- FUNÇÕES DE UPDATE DA IA ---

def update_process_ai(item_id, json_str):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # 1. Salva as specs detalhadas nas tabelas filhas
        persist_specs(item_id, json_str, conn)

        # 2. Prepara os dados resumidos para a tabela principal (olx_itens_raw)

        # Tratamento CPU
        cpu_data = json_str.get('cpu')
        cpu_str = "N/A"
        if isinstance(cpu_data, dict):
            if cpu_data.get('fabricante') == "UNFIT":
                cpu_str = "UNFIT"
            else:
                parts = [cpu_data.get('fabricante'), cpu_data.get('familia'), cpu_data.get('modelo')]
                cpu_str = " ".join([str(p) for p in parts if p]).strip()
        elif isinstance(cpu_data, str):
            cpu_str = cpu_data

        # Tratamento GPU
        gpu_data = json_str.get('gpu')
        gpu_str = "N/A"
        if isinstance(gpu_data, dict):
            parts = [gpu_data.get('fabricante_chip'), gpu_data.get('modelo')]
            gpu_str = " ".join([str(p) for p in parts if p]).strip()
        elif isinstance(gpu_data, str):
            gpu_str = gpu_data

        def safe_str(val):
            if isinstance(val, dict):
                return str(val)
            if val is None:
                return None
            return str(val)

        ram = safe_str(json_str.get('ram'))
        ram_tech = safe_str(json_str.get('ram_tech'))
        storage = safe_str(json_str.get('storage'))
        storage_type = safe_str(json_str.get('storage_type'))

        cursor.execute(
            """
            UPDATE olx_itens_raw
            SET cpu = %s, gpu = %s, ram = %s, ram_tech = %s, storage = %s, storage_type = %s, ai_check = 1
            WHERE id = %s
            """,
            (cpu_str, gpu_str, ram, ram_tech, storage, storage_type, item_id),
        )

        conn.commit()
    except psycopg2.Error as e:
        conn.rollback()
        print(f"Erro Update AI ID {item_id}: {e}")
    finally:
        conn.close()


def persist_specs(item_id, json_str, conn):
    cursor = conn.cursor()

    # --- Extração CPU ---
    cpu_data = json_str.get('cpu') or {}
    if isinstance(cpu_data, dict):
        c_maker = cpu_data.get('fabricante')
        c_fam = cpu_data.get('familia')
        c_model = cpu_data.get('modelo')
        c_gen = cpu_data.get('geracao')
        c_sock = cpu_data.get('socket')
        c_extra = cpu_data.get('spec_extra')

        cursor.execute(
            """
            INSERT INTO cpu_specs
            (id_olxtable, fabricante, familia, modelo, geracao, socket, spec_extra)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            """,
            (item_id, c_maker, c_fam, c_model, c_gen, c_sock, c_extra),
        )

    # --- Extração GPU ---
    gpu_data = json_str.get('gpu') or {}
    if isinstance(gpu_data, dict):
        g_chip = gpu_data.get('fabricante_chip')
        g_maker = gpu_data.get('montadora')
        g_line = gpu_data.get('linha')
        g_model = gpu_data.get('modelo')
        g_vram = gpu_data.get('vram')
        g_extras = gpu_data.get('extras')

        cursor.execute(
            """
            INSERT INTO gpu_specs
            (id_olxtable, fabricante_chip, montadora, linha, modelo, vram, extras)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            """,
            (item_id, g_chip, g_maker, g_line, g_model, g_vram, g_extras),
        )
