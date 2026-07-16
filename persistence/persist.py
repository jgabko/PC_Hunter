"""
Camada de persistência local (SQLite) do scraper de PCs da OLX.

Tabelas:

  OLX_ITENS_RAW
    id (pk), title, price, link (unique), cpu, ram, ram_tech, gpu, storage,
    storage_type, city, area, details, date_publish,
    latest (1 = versão mais recente do anúncio; 0 = versão antiga arquivada
            quando o mesmo link reaparece com dados diferentes),
    ai_check (0 = specs ainda não passaram pelo pipeline regex/IA; 1 = já passou)

  CPU_SPECS / GPU_SPECS
    tabelas filhas (fk id_olxTable -> OLX_ITENS_RAW.id) com as specs
    detalhadas extraídas pelo pipeline híbrido (regex + IA) em specs_AI.py.

NOTA (corrigido): este arquivo tinha o próprio conteúdo colado duas vezes
(um copy/paste acidental dentro de `persist_specs`), redefinindo todas as
funções do módulo dentro de um escopo local nunca usado. Esse bloco morto
foi removido — o comportamento é o mesmo, só sem o lixo de ~180 linhas.
"""
import sqlite3
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import DB_NAME


# --- CONFIGURAÇÃO E INICIALIZAÇÃO ---

def persist_init():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Tabela Principal
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS OLX_ITENS_RAW (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            price FLOAT,
            link VARCHAR(2083) NOT NULL UNIQUE,
            cpu TEXT,
            ram TEXT,
            ram_tech TEXT,
            gpu TEXT,
            storage TEXT,
            storage_type TEXT,
            city TEXT,
            area TEXT,
            details TEXT,
            date_publish DATE,
            latest INTEGER DEFAULT 1,
            ai_check INTEGER DEFAULT 0
        )
    ''')

    # Criar tabelas de specs aqui para evitar recriar toda vez
    specs_createTable(conn, cursor)

    conn.commit()
    return conn


def specs_createTable(conn, cursor):
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS CPU_SPECS (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_olxTable INTEGER NOT NULL,
            fabricante TEXT,
            familia TEXT,
            modelo  TEXT,
            geracao TEXT,
            socket TEXT,
            spec_extra TEXT 
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS GPU_SPECS (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_olxTable INTEGER NOT NULL,
            fabricante_chip TEXT,
            montadora TEXT,
            linha TEXT,
            modelo TEXT,
            vram TEXT,
            extras TEXT
        )
    ''')


# --- FUNÇÕES DE INSERÇÃO RAW (SCRAPING) ---

def persist(title, price, link, specs, local, details):
    conn = persist_init()
    cursor = conn.cursor()
    try:
        persist_item(conn, cursor, title, price, link, specs, local, details)
    finally:
        conn.close()


def persist_item(conn, cursor, title, price, link, specs, local, details):
    gpu = specs.get('gpu')
    ram = specs.get('ram')
    cpu = specs.get('cpu')
    storage = specs.get('storage')
    city = local.get('cidade')
    area = local.get('bairro')
    description = details.get('Descrição')

    existence = check_exits(conn, link)

    try:
        if existence:
            # Arquiva o anúncio antigo (latest=0) e insere o novo como latest=1
            cursor.execute("UPDATE OLX_ITENS_RAW SET latest=0 WHERE link=? AND latest=1;", (link,))

        cursor.execute("""
            INSERT OR IGNORE INTO OLX_ITENS_RAW 
            (title, price, link, cpu, ram, gpu, storage, city, area, details, date_publish, latest, ai_check) 
            VALUES (?,?,?,?,?,?,?,?,?,?,datetime('now', 'localtime'),1,0)
        """, (title, price, link, cpu, ram, gpu, storage, city, area, description))

        conn.commit()
    except sqlite3.Error as e:
        print(f"Erro SQL ao persistir item: {e}")


def check_exits(conn, link):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM OLX_ITENS_RAW WHERE link=?;", (link,))
    return cursor.fetchall()


def search_pending_items():
    conn = persist_init()  # garante que a tabela existe, mesmo em banco novo
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    # Pega apenas o essencial
    cursor.execute("SELECT id, title, details FROM OLX_ITENS_RAW WHERE ai_check = 0")
    rows = cursor.fetchall()
    conn.close()
    return rows


def persist_view():
    conn = persist_init()
    try:
        df = pd.read_sql_query("SELECT * FROM OLX_ITENS_RAW ORDER BY id DESC LIMIT 5", conn)
        print(df)
    except Exception:
        print("Banco vazio ou erro de leitura.")
    finally:
        conn.close()


# --- FUNÇÕES DE UPDATE DA IA ---

def update_process_ai(item_id, json_str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        # 1. Salva as specs detalhadas nas tabelas filhas
        persist_specs(item_id, json_str, conn)

        # 2. Prepara os dados resumidos para a tabela principal (OLX_ITENS_RAW)
        # Converte dicionários em string para não dar erro no SQLite

        # Tratamento CPU
        cpu_data = json_str.get('cpu')
        cpu_str = "N/A"
        if isinstance(cpu_data, dict):
            if cpu_data.get('fabricante') == "UNFIT":
                cpu_str = "UNFIT"
            else:
                parts = [cpu_data.get('fabricante'), cpu_data.get('familia'), cpu_data.get('modelo')]
                # Filtra Nones e junta com espaço
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

        # Tratamento RAM/Storage (garante string ou None, nunca dict)
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

        cursor.execute("""
            UPDATE OLX_ITENS_RAW 
            SET cpu = ?, gpu = ?, ram = ?, ram_tech= ?, storage = ?, storage_type=?, ai_check = 1 
            WHERE id = ?
        """, (cpu_str, gpu_str, ram, ram_tech, storage, storage_type, item_id))

        conn.commit()
    except sqlite3.Error as e:
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

        cursor.execute('''
            INSERT OR IGNORE INTO CPU_SPECS 
            (id_olxTable, fabricante, familia, modelo, geracao, socket, spec_extra) 
            VALUES (?,?,?,?,?,?,?) 
        ''', (item_id, c_maker, c_fam, c_model, c_gen, c_sock, c_extra))

    # --- Extração GPU ---
    gpu_data = json_str.get('gpu') or {}
    if isinstance(gpu_data, dict):
        g_chip = gpu_data.get('fabricante_chip')
        g_maker = gpu_data.get('montadora')
        g_line = gpu_data.get('linha')
        g_model = gpu_data.get('modelo')
        g_vram = gpu_data.get('vram')
        g_extras = gpu_data.get('extras')

        cursor.execute('''
            INSERT OR IGNORE INTO GPU_SPECS
            (id_olxTable, fabricante_chip, montadora, linha, modelo, vram, extras) 
            VALUES (?,?,?,?,?,?,?) 
        ''', (item_id, g_chip, g_maker, g_line, g_model, g_vram, g_extras))
