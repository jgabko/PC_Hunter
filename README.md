# OLX PC Hunter

Scraper de anúncios de PC na OLX, com extração de specs (regex + IA),
persistência local em SQLite, limpeza automática de anúncios expirados e
um dashboard Streamlit para achar oportunidades de compra/revenda.

## Estrutura do projeto

```
config.py              # Configuração central (.env) - URLs, nome do banco, chaves de API
pipeline.py             # Orquestrador: scraping -> limpeza -> pronto para o dashboard
dashboard.py            # Dashboard Streamlit (flips e "fusões" de PCs)
flipper.py               # Cálculo de score/ranking dos PCs (usa benchmarks.py)
benchmarks.py            # Base de benchmarks de CPU/GPU/RAM/Storage
cleaner.py                # Verifica e remove anúncios vendidos/expirados
clean_db.py               # Corrige registros com dados corrompidos

scraping/                # Coleta das páginas de listagem e detalhe da OLX
  olx.py                    # Loop principal do scraper
  olx_detail_page.py         # Extração da página de detalhe de um anúncio

processing/               # Transformação dos dados brutos
  specs.py                    # Extração de specs via regex (CPU/GPU/RAM/Storage)
  specs_AI.py                  # Pipeline híbrido: regex primeiro, IA (Groq/Ollama) no que sobrar

schema/                   # Validação
  schema.py                    # Modelo Pydantic que barra itens sem preço/link

persistence/               # Acesso a dados
  persist.py                    # Camada de acesso ao SQLite (olx.db)
```

## Configuração inicial

1. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```
2. Copie `.env.example` para `.env` e preencha sua chave da Groq:
   ```
   cp .env.example .env
   ```
   > Se você usou este projeto antes desta reorganização, **revogue** a chave
   > antiga da Groq (ela estava exposta em texto puro no código-fonte) e gere
   > uma nova em https://console.groq.com/keys.

## Uso

Rodar o pipeline completo (scraping + limpeza):
```
python pipeline.py
```

Rodar só o scraper:
```
python -m scraping.olx
```

Rodar o dashboard:
```
streamlit run dashboard.py
```

## Notas de migração (desta reorganização)

- Os módulos que antes ficavam soltos na raiz (`Persist.py`, `olx_detail_page.py`,
  `specs.py`, `specs_AI.py`, `schema.py`) agora vivem em pacotes (`persistence/`,
  `scraping/`, `processing/`, `schema/`), no mesmo espírito da separação de
  responsabilidades usada no projeto ImobData.
- `Persist.py` virou `persistence/persist.py` (nome de módulo em minúsculas,
  convenção PEP 8) — se você tinha scripts próprios importando `import Persist`,
  troque para `from persistence import persist`.
- O nome do arquivo do banco (`olx.db`) e a URL base de busca agora vêm de
  `config.py` / `.env`, em vez de estarem hardcoded em cada arquivo.
