import re


def parse_specs(titulo, details):
    # Garante que details seja um dicionário
    if not isinstance(details, dict):
        details = {'Descrição': ''}

    details_text = details.get('Descrição', '')

    # Combina título e descrição
    # Remove acentos básicos e deixa maiúsculo para padronizar
    text_full = f"{titulo} {details_text}".upper()

    # Limpeza básica: troca barras e quebras de linha por espaço
    text_clean = re.sub(r'[/|\\\n\r]', ' ', text_full)
    # Remove múltiplos espaços
    text_clean = re.sub(r'\s+', ' ', text_clean)

    specs = {
        'cpu': 'N/A',
        'ram': 'N/A',
        'gpu': 'N/A',
        'storage': 'N/A'
    }

    # ================= (1. CPU) ================= #
    # Lista ordenada do mais específico para o mais genérico
    cpu_patterns = [
        r'RYZEN\s*[3579]\s*\d{4}[GX]?',  # Ryzen 5 5600G
        r'RYZEN\s*[3579]',  # Ryzen 5
        r'ATHLON\s*\d{3,4}[GE]?',  # Athlon 3000G
        r'(?:CORE\s*)?I[3579][\s-]?\d{3,5}\w?',  # i5 10400, Core i3-9100f
        r'XEON\s*E5\s*[\w-]+(?:\s*V\d)?',  # Xeon E5 2650 v3
        r'XEON\s*[\w-]+',  # Xeon genérico
        r'PENTIUM\s*\w{0,5}\s*\d{3,4}',  # Pentium Gold G5400
        r'FX[\s-]?\d{4}'  # FX 6300
    ]

    for pat in cpu_patterns:
        match = re.search(pat, text_clean)
        if match:
            specs['cpu'] = match.group(0).strip()
            break

    # ================= (2. MEMÓRIA RAM) ================= #
    # Regex melhorado para "8Ram", "16 gigas", "8gb"
    ram_candidates = []

    # Padrão 1: Número seguido de unidade e depois indicador de memória
    # Ex: 16GB RAM, 16 GIGAS RAM, 8 GB DDR4
    p1 = re.findall(r'\b(\d{1,3})\s*(?:GB|G|GIGAS?)\s*(?:DDR\d|RAM|MEM)', text_clean)

    # Padrão 2: Indicador de memória antes
    # Ex: RAM 16GB, Memoria: 8gb
    p2 = re.findall(r'(?:RAM|MEM[ÓO]RIA).{0,5}[:]?\s*(\d{1,3})\s*(?:GB|G|GIGAS?)', text_clean)

    # Padrão 3: "8Ram" (colado) ou "16Gb" isolado se tiver contexto de PC
    p3 = re.findall(r'\b(\d{1,3})\s*RAM', text_clean)

    ram_candidates.extend(p1)
    ram_candidates.extend(p2)
    ram_candidates.extend(p3)

    valid_rams = []
    if ram_candidates:
        for r in ram_candidates:
            try:
                val = int(r)
                # Filtra valores absurdos para RAM de PC (entre 2 e 128)
                if val in [2, 4, 6, 8, 10, 12, 16, 20, 24, 32, 48, 64, 128]:
                    valid_rams.append(val)
            except:
                continue

    if valid_rams:
        specs['ram'] = f"{max(valid_rams)} GB"

    # ================= (3. ARMAZENAMENTO) ================= #
    storage_found = set()

    # Regex flexível para pares (TIPO CAPACIDADE) ou (CAPACIDADE TIPO)
    # Unidade aceita: TB, T, GB, G, GIGAS

    # Procura: SSD 240 GB, HD 1 TB, NVME 500 GIGAS
    pat_storage_A = r'(SSD|NVME|HD|HDD|M\.2|SATA)\s*(?:DE\s*)?(\d{1,4})\s*(TB|T|GB|G|GIGAS?)'
    matches_A = re.findall(pat_storage_A, text_clean)

    # Procura: 240 GB SSD, 1TB HD
    pat_storage_B = r'(\d{1,4})\s*(TB|T|GB|G|GIGAS?)\s*(?:DE\s*)?(SSD|NVME|HD|HDD|M\.2|SATA)'
    matches_B = re.findall(pat_storage_B, text_clean)

    def format_storage(tipo, num, unit):
        try:
            val = int(num)
            u_clean = 'GB'
            if unit.startswith('T'):
                u_clean = 'TB'
            elif val < 60 and u_clean == 'GB':
                # Ignora valores baixos em GB (pendrives ou erros de leitura)
                return None

            tipo_clean = tipo.replace('HDD', 'HD')
            return f"{tipo_clean} {val}{u_clean}"
        except:
            return None

    for m in matches_A:
        s = format_storage(m[0], m[1], m[2])
        if s: storage_found.add(s)

    for m in matches_B:
        s = format_storage(m[2], m[0], m[1])
        if s: storage_found.add(s)

    if storage_found:
        specs['storage'] = ', '.join(list(storage_found))

    # ================= (4. PLACA DE VÍDEO) ================= #
    # Ordem: Modelos específicos -> Famílias genéricas

    # RTX, GTX, RX (Ex: RTX 3060, RX 580)
    gpu_pat_main = r'(RTX|GTX|RX|RADEON)\s*[-]?\s*(\d{3,4}\s*(?:TI|SUPER|XT|OC|SE)?)'
    gpu_match = re.search(gpu_pat_main, text_clean)

    if gpu_match:
        specs['gpu'] = f"{gpu_match.group(1)} {gpu_match.group(2)}"
    else:
        # Padrões secundários / Antigos / Integrados
        others = [
            r'GT\s*\d{3,4}',  # GT 710, GT 1030
            r'VEGA\s*\d+',  # Vega 7, Vega 11
            r'HD\s*GRAPHICS',  # Intel HD
            r'HD\s*\d{4}',  # HD 7770 (Antigas AMD)
            r'R[579]\s*\d{3}',  # R7 260x
            r'ARC\s*A\d{3}'  # Intel Arc
        ]
        for pat in others:
            m = re.search(pat, text_clean)
            if m:
                specs['gpu'] = m.group(0)
                break

    return specs


# --- Funções Auxiliares ---
def parse_loc(text_loc):
    if not text_loc: return {'cidade': 'N/A', 'bairro': None}
    pattern = r"^(.*?)(?:,\s*(.*))?$"
    match = re.search(pattern, text_loc)
    if match:
        return {'cidade': match.group(1).strip(), 'bairro': match.group(2).strip() if match.group(2) else None}
    return {'cidade': text_loc, 'bairro': None}


def parse_price(text_price):
    if not text_price: return 0
    num = re.sub(r'\D', '', text_price)
    try:
        return int(num)
    except:
        return 0