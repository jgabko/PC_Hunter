import json
import ollama
import re
import time
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from groq import Groq

# Garante a raiz do projeto no sys.path (mesmo motivo do scraping/olx.py)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Suas importações
from persistence.persist import update_process_ai
from persistence.persist import search_pending_items
from config import GROQ_API_KEY, USE_GROQ

# --- CONFIGURAÇÃO DE VELOCIDADE ---
MAX_WORKERS = 1  # Reduzi para 1 para garantir estabilidade. Se quiser arriscar, coloque 2.


# --- 1. FILTRO RÁPIDO (REGEX) ---
def try_fast_extract(title, details):
    """
    Tenta extrair dados sem usar IA. Retorna JSON ou None.
    Custo: 0ms
    """
    text = f"{title} {details}".lower()

    # Regex para CPU
    cpu_match = re.search(r'\b(ryzen\s?(\d)|core\s?i(\d)|i(\d)|xeon)\s?-?\s?(\d{4,5}[a-z]?)?', text)
    # Regex para GPU
    gpu_match = re.search(r'\b(rtx|gtx|rx)\s?(\d{3,4})\s?(ti|super|xt)?', text)

    # Só aceitamos se achar GPU
    if gpu_match:
        gpu_model = f"{gpu_match.group(1)} {gpu_match.group(2)} {gpu_match.group(3) or ''}".upper().strip()

        cpu_model = "N/A"
        if cpu_match:
            raw_fam = cpu_match.group(1).replace(" ", "")
            raw_mod = cpu_match.group(5) or ""
            cpu_model = f"{raw_fam} {raw_mod}".upper()

        return {
            "cpu": {"modelo": cpu_model, "fabricante": "DETECTED_REGEX", "familia": "", "geracao": "", "socket": "",
                    "spec_extra": ""},
            "gpu": {"modelo": gpu_model, "fabricante_chip": "DETECTED_REGEX", "montadora": "", "linha": "", "vram": "",
                    "extras": ""},
            "ram": None, "ram_tech": None, "storage": None, "storage_type": None
        }

    return None


# --- 2. PREPARAÇÃO DO LOTE ---
def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))


def generate_merged_prompt(items_chunk):
    input_text = ""
    for item in items_chunk:
        input_text += f"[[[ITEM_{item['id']}]]]\nT:{item['title']}\nD:{item['details'][:150]}\n[[[END]]]\n"

    return f"""
Converter lista para JSON.
REGRAS:
1. Saída: {{ "itens": [ ... ] }}
2. Se não for PC: cpu="UNFIT"

EXEMPLO:
[[[ITEM_10]]] T: PC i5 D: 8gb [[[END]]]
-> {{ "itens": [ {{ "id": 10, "cpu": {{ "modelo": "i5" }}, "gpu": {{ "modelo": null }} }} ] }}

ENTRADA:
{input_text}
"""


# --- 3. PROCESSAMENTO DA IA (COM RETRY) ---
def call_ai_api(prompt, retries=5):
    """
    Chama a IA com lógica de tentativa automática se der erro de limite (429)
    """
    if USE_GROQ and not GROQ_API_KEY:
        raise ValueError(
            "USE_GROQ está ativado mas GROQ_API_KEY não foi encontrada no .env. "
            "Copie .env.example para .env e preencha a chave, ou defina USE_GROQ=false "
            "no .env para usar o Ollama local."
        )

    for attempt in range(retries):
        try:
            if USE_GROQ:
                client = Groq(api_key=GROQ_API_KEY)
                completion = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                    response_format={"type": "json_object"}
                )
                return completion.choices[0].message.content
            else:
                response = ollama.chat(
                    model='llama3.2',
                    format='json',
                    messages=[{'role': 'user', 'content': prompt}],
                    options={'temperature': 0}
                )
                return response['message']['content']

        except Exception as e:
            error_msg = str(e)
            # Se for erro de Rate Limit, espera
            if "429" in error_msg or "Rate limit" in error_msg:
                wait_time = 15 * (attempt + 1)
                print(f"   [RATE LIMIT] Esperando {wait_time}s para tentar de novo...")
                time.sleep(wait_time)
            else:
                print(f"   [ERRO IA] {e}")
                return None  # Outros erros não tentamos de novo
    return None


def process_single_batch(batch):
    """Processa UM lote e retorna quantos foram salvos"""
    ids_batch = [i['id'] for i in batch]

    prompt = generate_merged_prompt(batch)

    response_content = call_ai_api(prompt)
    if not response_content:
        return 0

    try:
        parsed_json = json.loads(response_content)

        items_list = []
        if isinstance(parsed_json, dict):
            items_list = parsed_json.get("itens", [])
            if not items_list and "id" in parsed_json:
                items_list = [parsed_json]
        elif isinstance(parsed_json, list):
            items_list = parsed_json

        count_saved = 0
        for ai_item in items_list:
            item_id = ai_item.get('id')
            if item_id in ids_batch:
                if ai_item.get('cpu') == "UNFIT":
                    ai_item['cpu'] = {"fabricante": "UNFIT", "modelo": "UNFIT"}

                update_process_ai(item_id, ai_item)
                count_saved += 1
        return count_saved

    except Exception as e:
        print(f"Erro no Parse JSON Batch {ids_batch}: {e}")
        return 0


# --- 4. FUNÇÃO DE PROGRESSO ---
def print_progress(current, total, prefix="Progresso"):
    percent = (current / total) * 100
    print(f"[{prefix}] {current} de {total} - {percent:.1f}% Concluído")


# --- 5. CONTROLADOR PRINCIPAL ---
def process_pipeline(rows, batch_size=5):
    total_itens = len(rows)
    print(f"=== INICIANDO PIPELINE HÍBRIDO: {total_itens} itens no total ===")

    ai_queue = []
    regex_count = 0
    processed_count = 0

    # --- FASE 1: FILTRO REGEX ---
    print("\n--- Fase 1: Análise Rápida (Regex) ---")

    for index, r in enumerate(rows, 1):
        fast_data = try_fast_extract(r['title'], r['details'] or "")

        if fast_data:
            fast_data['id'] = r['id']
            update_process_ai(r['id'], fast_data)
            regex_count += 1
            print_progress(index, total_itens, prefix="REGEX")
        else:
            ai_queue.append({'id': r['id'], 'title': r['title'], 'details': r['details'] or ""})

    print(f"\n--- Resumo Fase 1: {regex_count} resolvidos via Regex. Restam {len(ai_queue)} para IA ---")

    # --- FASE 2: IA EM PARALELO ---
    if ai_queue:
        total_ai_items = len(ai_queue)
        print(f"\n--- Fase 2: Processamento IA ({total_ai_items} itens) ---")

        batches = list(chunker(ai_queue, batch_size))
        items_processed_ai = 0

        if USE_GROQ:
            print(f"   -> Modo TURBO: {MAX_WORKERS} threads (com Retry Automático)")

            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                future_to_batch = {executor.submit(process_single_batch, batch): batch for batch in batches}

                for future in as_completed(future_to_batch):
                    batch = future_to_batch[future]
                    try:
                        saved_count = future.result()
                        items_processed_ai += len(batch)
                        print_progress(items_processed_ai, total_ai_items, prefix="IA GROQ")
                    except Exception as exc:
                        print(f"Lote gerou exceção: {exc}")
        else:
            print("   -> Modo LOCAL: Sequencial (Ollama)")
            for batch in batches:
                process_single_batch(batch)
                items_processed_ai += len(batch)
                print_progress(items_processed_ai, total_ai_items, prefix="IA LOCAL")

    print("\n=== PIPELINE FINALIZADO COM SUCESSO ===")


if __name__ == "__main__":
    rows = search_pending_items()
    if rows:
        # Batch size 5 é seguro para evitar rate limits
        process_pipeline(rows, batch_size=5)
    else:
        print("Nenhum item pendente.")