"""
Configuração central do projeto.

Segue o mesmo padrão do ImobData (persistence/supabase_f.py): as credenciais
NUNCA ficam hardcoded no código-fonte, apenas em variáveis de ambiente
carregadas de um arquivo .env (que fica no .gitignore e nunca é commitado).

Uso:
    from config import GROQ_API_KEY, USE_GROQ, DATABASE_URL

Antes de rodar o projeto, copie .env.example para .env e preencha os valores.

IMPORTANTE: este módulo é importado por muita coisa que não tem nada a ver
com IA (persistence/persist.py, flipper.py, cleaner.py só querem a
DATABASE_URL). Por isso NÃO validamos a chave da Groq aqui — isso travaria
o resto do projeto mesmo sem nenhum problema real. Quem realmente precisa
da chave (processing/specs_AI.py) valida na hora de usar.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# --- IA (Groq / Ollama) ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
USE_GROQ = os.environ.get("USE_GROQ", "true").lower() == "true"

# --- Scraper ---
BASE_URL = os.environ.get("OLX_BASE_URL", "https://www.olx.com.br/estado-pr?q=pc")

# --- Banco de dados (Postgres/Supabase) ---
# Connection string completa, pega em Supabase > Project Settings > Database
# > Connection string (modo "URI"). Formato:
#   postgresql://postgres:[SUA-SENHA]@[HOST]:5432/postgres
#
# Substituiu a antiga DB_NAME (nome do arquivo .db do SQLite) — não existe
# mais arquivo de banco local, então essa variável não tem valor-padrão:
# se faltar, quem tentar conectar recebe um erro claro na hora, em vez de
# silenciosamente tentar abrir um arquivo local que não existe mais.
DATABASE_URL = os.environ.get("DATABASE_URL")

# --- API / CORS ---
# Domínios que podem chamar a API (o frontend em produção, ex: Vercel).
# Lista separada por vírgula em FRONTEND_ORIGINS, ex:
#   FRONTEND_ORIGINS=https://pc-hunter.vercel.app,https://www.seudominio.com
# Sem essa variável, cai no comportamento de dev local (Vite na 5173).
_default_origins = "http://localhost:5173,http://127.0.0.1:5173"
FRONTEND_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("FRONTEND_ORIGINS", _default_origins).split(",")
    if origin.strip()
]