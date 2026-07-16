"""
Pipeline completo do OLX PC Hunter, no mesmo espírito do pipeline.py do
ImobData: várias etapas encadeadas, cada uma isolada por try/except para
que a falha de uma etapa não impeça as seguintes de rodar.

  1) Raspagem (scraping + validação Pydantic + pipeline híbrido regex/IA)
  2) Limpeza: remove do banco anúncios que já saíram do ar (vendidos/expirados)
  3) Deixa o banco pronto para o dashboard (streamlit run dashboard.py)

Uso:
  python pipeline.py
"""
import sys
from pathlib import Path

# Garante que a raiz do projeto seja encontrada, não importa de onde este
# script seja executado (mesmo padrão do pipeline.py do ImobData).
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from scraping.olx import main as rodar_scraper   # noqa: E402
from cleaner import Cleaner                       # noqa: E402


def _titulo(texto: str):
    print("\n" + "=" * 60)
    print(f" {texto}")
    print("=" * 60)


def executar_pipeline_completo(rodar_limpeza: bool = True):
    _titulo("INICIANDO PIPELINE COMPLETO - OLX -> BANCO -> LIMPEZA -> DASHBOARD")

    # ------------------------------------------------------------
    # PASSO 1: Scraping + validação + pipeline híbrido (regex/IA)
    # ------------------------------------------------------------
    print("\n>>> PASSO 1: Raspando anúncios novos...")
    try:
        rodar_scraper()
    except Exception as e:
        print(f"❌ Falha na etapa de scraping: {e}")

    # ------------------------------------------------------------
    # PASSO 2: Limpeza de anúncios expirados/vendidos (não bloqueia o pipeline)
    # ------------------------------------------------------------
    if rodar_limpeza:
        print("\n>>> PASSO 2: Verificando anúncios expirados/vendidos...")
        try:
            Cleaner().run_cleaning_cycle()
        except Exception as e:
            print(f"⚠️ Falha ao limpar banco (etapa não bloqueante, seguindo em frente): {e}")
    else:
        print("\n>>> PASSO 2: Limpeza pulada (rodar_limpeza=False).")

    _titulo("PIPELINE COMPLETO FINALIZADO!")
    print("Dashboard pronto para refletir os novos dados: streamlit run dashboard.py\n")


if __name__ == "__main__":
    executar_pipeline_completo()
