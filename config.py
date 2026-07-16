"""
Configuração central do projeto.

Segue o mesmo padrão do ImobData (persistence/supabase_f.py): as credenciais
NUNCA ficam hardcoded no código-fonte, apenas em variáveis de ambiente
carregadas de um arquivo .env (que fica no .gitignore e nunca é commitado).

Uso:
    from config import GROQ_API_KEY, USE_GROQ

Antes de rodar o projeto, copie .env.example para .env e preencha os valores.

IMPORTANTE: este módulo é importado por muita coisa que não tem nada a ver
com IA (dashboard.py, flipper.py, cleaner.py só querem o DB_NAME). Por isso
NÃO validamos a chave da Groq aqui — isso travaria o dashboard mesmo sem
nenhum problema real. Quem realmente precisa da chave (processing/specs_AI.py)
valida na hora de usar.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# --- IA (Groq / Ollama) ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
USE_GROQ = os.environ.get("USE_GROQ", "true").lower() == "true"

# --- Scraper ---
BASE_URL = os.environ.get("OLX_BASE_URL", "https://www.olx.com.br/estado-pr?q=pc")
DB_NAME = os.environ.get("DB_NAME", "olx.db")

