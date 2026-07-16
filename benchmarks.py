from thefuzz import process


class BenchmarkLoader:
    def __init__(self):
        # === BANCO DE DADOS DE CPUS (Baseado no seu relatório) ===
        self.cpu_db = {
            # --- Intel 12ª Geração (Alder Lake) ---
            "intel core i9 12900k": 41500, "intel core i7 12700k": 34500,
            "intel core i5 12600k": 27500, "intel core i5 12400f": 19500,
            "intel core i3 12100f": 14100, "pentium gold g7400": 6710,

            # --- Intel 10ª e 11ª Geração ---
            "intel core i9 11900k": 25500, "intel core i7 11700k": 24600,
            "intel core i5 11600k": 19800, "intel core i5 11400f": 17447,
            "intel core i9 10900k": 23500, "intel core i7 10700k": 19292,
            "intel core i7 10700": 17300, "intel core i5 10600k": 14500,
            "intel core i5 10400f": 12450, "intel core i3 10105f": 8950,
            "intel core i3 10100f": 8717, "pentium gold g6400": 4180,

            # --- Intel 8ª e 9ª Geração ---
            "intel core i9 9900k": 18500, "intel core i7 9700k": 14550,
            "intel core i7 9700": 13500, "intel core i5 9600k": 10800,
            "intel core i5 9400f": 9500, "intel core i3 9100f": 6706,
            "intel core i7 8700k": 13890, "intel core i7 8700": 13050,
            "intel core i5 8600k": 10141, "intel core i5 8400": 9229,
            "intel core i3 8100": 6065, "pentium gold g5400": 3732,

            # --- Intel Clássicos (2ª a 7ª Gen) ---
            "intel core i7 7700k": 9700, "intel core i7 7700": 8650,
            "intel core i5 7600k": 6850, "intel core i5 7500": 6050,
            "intel core i5 7400": 5500, "intel core i3 7100": 4310,
            "intel core i7 6700k": 8950, "intel core i7 6700": 8100,
            "intel core i5 6600k": 6300, "intel core i5 6500": 5650,
            "intel core i5 6400": 5173, "intel core i3 6100": 4100,
            "pentium g4560": 3500,
            "intel core i7 4790k": 8050, "intel core i7 4790": 7220,
            "intel core i7 4770k": 7160, "intel core i7 4770": 7040,
            "intel core i5 4690k": 5650, "intel core i5 4590": 5315,
            "intel core i5 4570": 5234, "intel core i5 4460": 4794,
            "intel core i3 4170": 3550, "intel core i3 4130": 3338,
            "intel core i7 3770k": 6380, "intel core i7 3770": 6320,
            "intel core i5 3570k": 4918, "intel core i5 3570": 4929,
            "intel core i5 3470": 4662, "intel core i3 3240": 2890,
            "intel core i3 3220": 2850,
            "intel core i7 2700k": 5520, "intel core i7 2600k": 5490,
            "intel core i7 2600": 5344, "intel core i5 2500k": 4155,
            "intel core i5 2500": 4090, "intel core i5 2400": 3866,
            "intel core i3 2120": 2190, "intel core i3 2100": 1860,

            # --- AMD Ryzen 5000 ---
            "amd ryzen 9 5950x": 46000, "amd ryzen 9 5900x": 39500,
            "amd ryzen 7 5800x3d": 28500, "amd ryzen 7 5800x": 28000,
            "amd ryzen 7 5700x": 26800, "amd ryzen 7 5700g": 24327,
            "amd ryzen 5 5600x": 22100, "amd ryzen 5 5600": 21540,
            "amd ryzen 5 5600g": 19760, "amd ryzen 5 5500": 19570,
            "amd ryzen 5 4600g": 15980, "amd ryzen 5 4500": 16015,
            "amd ryzen 3 4100": 11300,

            # --- AMD Ryzen 1000, 2000, 3000 ---
            "amd ryzen 9 3900x": 32800, "amd ryzen 7 3800x": 23600,
            "amd ryzen 7 3700x": 22800, "amd ryzen 5 3600x": 18540,
            "amd ryzen 5 3600": 17800, "amd ryzen 5 3500x": 13360,
            "amd ryzen 5 3400g": 9360, "amd ryzen 3 3300x": 12800,
            "amd ryzen 3 3200g": 7200, "amd ryzen 7 2700x": 17450,
            "amd ryzen 7 2700": 15300, "amd ryzen 5 2600x": 14050,
            "amd ryzen 5 2600": 13200, "amd ryzen 5 2400g": 8750,
            "amd ryzen 3 2200g": 6800, "amd ryzen 7 1800x": 16280,
            "amd ryzen 7 1700x": 15500, "amd ryzen 7 1700": 13470,
            "amd ryzen 5 1600x": 13060, "amd ryzen 5 1600": 12350,
            "amd ryzen 5 1500x": 9060, "amd ryzen 5 1400": 7820,
            "amd ryzen 3 1300x": 6950, "amd ryzen 3 1200": 6250,
            "amd athlon 3000g": 4443, "amd athlon 200ge": 4150,

            # --- Xeons (AliExpress/Servidor) ---
            "intel xeon e5 2699 v3": 22350, "intel xeon e5 2696 v3": 22500,
            "intel xeon e5 2678 v3": 16900, "intel xeon e5 2666 v3": 14040,
            "intel xeon e5 2650 v4": 15900, "intel xeon e5 2640 v4": 13500,
            "intel xeon e5 2640 v3": 10800, "intel xeon e5 2630 v3": 9800,
            "intel xeon e5 2620 v4": 9200, "intel xeon e5 2620 v3": 7920
        }

        # === BANCO DE DADOS DE GPUS ===
        self.gpu_db = {
            # --- NVIDIA RTX ---
            "geforce rtx 4060": 19537,
            "geforce rtx 3060 ti": 20300,
            "geforce rtx 3060 12gb": 16755, "geforce rtx 3060": 16755,
            "geforce rtx 3050": 12519,
            "geforce rtx 2060 super": 16488, "geforce rtx 2060": 14115,

            # --- NVIDIA GTX Modernas ---
            "geforce gtx 1660 super": 12687, "geforce gtx 1660": 11500,
            "geforce gtx 1650": 7867,

            # --- NVIDIA Antigas/Entrada ---
            "geforce gtx 1060 6gb": 10200, "geforce gtx 1060 3gb": 9000,
            "geforce gtx 1050 ti": 6355, "geforce gtx 1050": 5500,
            "geforce gtx 960": 6134,
            "geforce gtx 750 ti": 3902,
            "geforce gt 1030": 2404,
            "geforce gt 710": 619,
            "geforce gt 730": 800,

            # --- AMD Radeon ---
            "radeon rx 7600": 16549,
            "radeon rx 6600": 15084,
            "radeon rx 580": 8792, "radeon rx 580 2048sp": 7628,
            "radeon rx 570": 6337,
            "radeon rx 550": 2680,

            # --- Gráficos Integrados (Importantíssimo para PCs baratos) ---
            "radeon vega 7": 2547,  # Ryzen 5600G
            "radeon vega 8": 1540,
            "radeon vega 11": 2091,
            "intel uhd 730": 1540,
            "intel uhd 630": 1230
        }

    def get_score(self, item_name, item_type='cpu'):
        """
        Recebe o nome sujo e retorna a pontuação.
        Inclui trava de segurança para processadores Intel.
        """
        if not item_name or len(str(item_name)) < 3:
            return 0

        # Normaliza a entrada
        query = str(item_name).lower().replace('-', ' ').strip()

        if "unfit" in query or "n/a" in query:
            return 0

        db = self.cpu_db if item_type == 'cpu' else self.gpu_db

        best_match = process.extractOne(query, db.keys(), score_cutoff=70)

        if best_match:
            name_found = best_match[0]
            score_val = db[name_found]

            # --- NOVA SEGURANÇA: Proteção Anti-Scam para Intel ---
            if item_type == 'cpu' and "intel" in name_found and "core" in name_found:
                # Extrai apenas os dígitos para comparar
                numeros_query = "".join(filter(str.isdigit, query))
                numeros_match = "".join(filter(str.isdigit, name_found))

                # Se o anúncio diz "i7" (sem numero, ex: len 1) e o match é "i7 8700" (len 5),
                # o fuzzy match foi "burro" e pegou qualquer coisa. Penaliza.
                if len(numeros_query) < 3 and len(numeros_match) >= 3:
                    # Retorna valor irrisório para não aparecer no topo
                    return 500

            return score_val

        return 0

    def get_ram_score(self, ram_val):
        """Calcula score extra baseado na quantidade de RAM"""
        try:
            # Tenta limpar string "16 GB" -> 16
            if isinstance(ram_val, str):
                nums = "".join(filter(str.isdigit, ram_val))
                gb = int(nums) if nums else 0
            else:
                gb = int(ram_val)

            # 200 pontos por GB de RAM
            return gb * 200
        except:
            return 0

    def get_storage_score(self, storage_str):
        """Bônus se tiver SSD/NVMe"""
        if not storage_str:
            return 0

        s = str(storage_str).upper()
        if "SSD" in s or "NVME" in s or "M.2" in s:
            return 2000
        return 0


if __name__ == "__main__":
    b = BenchmarkLoader()
    print("--- Teste de Reconhecimento ---")
    print(f"Texto: 'i7 genérico' -> Score: {b.get_score('i7', 'cpu')}")  # Deve dar baixo
    print(f"Texto: 'i7 8700' -> Score: {b.get_score('i7 8700', 'cpu')}")  # Deve dar alto
    print(f"RAM: '16 GB' -> Score: {b.get_ram_score('16 GB')}")
    print(f"Storage: 'SSD 240GB' -> Score: {b.get_storage_score('SSD 240GB')}")