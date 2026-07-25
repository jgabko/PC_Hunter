<div align="center">

  <h1>OLX PC Hunter</h1>

  <p>
    Scraper de anúncios de PC na OLX, com extração de specs (regex + IA),
    persistência local em SQLite, limpeza automática de anúncios expirados e
    um dashboard Streamlit para achar oportunidades de compra/revenda.
  </p>

<!-- Badges -->
<p>
  <a href="https://github.com/jgabko/PC_Hunter/graphs/contributors">
    <img src="https://img.shields.io/github/contributors/jgabko/PC_Hunter" alt="contributors" />
  </a>
  <a href="">
    <img src="https://img.shields.io/github/last-commit/jgabko/PC_Hunter" alt="last update" />
  </a>
  <a href="https://github.com/jgabko/PC_Hunter/network/members">
    <img src="https://img.shields.io/github/forks/jgabko/PC_Hunter" alt="forks" />
  </a>
  <a href="https://github.com/jgabko/PC_Hunter/stargazers">
    <img src="https://img.shields.io/github/stars/jgabko/PC_Hunter" alt="stars" />
  </a>
  <a href="https://github.com/jgabko/PC_Hunter/issues/">
    <img src="https://img.shields.io/github/issues/jgabko/PC_Hunter" alt="open issues" />
  </a>
</p>

<h4>
    <a href="https://github.com/jgabko/PC_Hunter/">Ver Demo</a>
  <span> · </span>
    <a href="https://github.com/jgabko/PC_Hunter">Documentação</a>
  <span> · </span>
    <a href="https://github.com/jgabko/PC_Hunter/issues/">Reportar Bug</a>
  <span> · </span>
    <a href="https://github.com/jgabko/PC_Hunter/issues/">Solicitar Feature</a>
  </h4>
</div>

<br />

<!-- Table of Contents -->
# Índice

- [Sobre o Projeto](#sobre-o-projeto)
  * [Tech Stack](#tech-stack)
  * [Funcionalidades](#funcionalidades)
  * [Variáveis de Ambiente](#variáveis-de-ambiente)
- [Getting Started](#getting-started)
  * [Pré-requisitos](#pré-requisitos)
  * [Instalação](#instalação)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Notas de Migração](#notas-de-migração)
- [Roadmap](#roadmap)
- [Licença](#licença)


<!-- About the Project -->
## Sobre o Projeto

O **OLX PC Hunter** coleta anúncios de PCs montados publicados na OLX,
extrai as especificações (CPU, GPU, RAM, armazenamento) usando regex com
fallback em IA, persiste tudo localmente em SQLite, remove automaticamente
anúncios vendidos/expirados e expõe um dashboard em Streamlit para ranquear
oportunidades de compra e revenda.

<!-- TechStack -->
### Tech Stack

<details>
  <summary>Coleta e Processamento</summary>
  <ul>
    <li><a href="https://www.python.org/">Python</a></li>
    <li>Regex (extração de specs)</li>
    <li><a href="https://groq.com/">Groq</a> / <a href="https://ollama.com/">Ollama</a> (IA, fallback de extração de specs)</li>
    <li><a href="https://docs.pydantic.dev/">Pydantic</a> (validação de schema)</li>
  </ul>
</details>

<details>
  <summary>Persistência e Visualização</summary>
  <ul>
    <li><a href="https://www.sqlite.org/">SQLite</a></li>
    <li><a href="https://streamlit.io/">Streamlit</a> (dashboard)</li>
  </ul>
</details>

<!-- Features -->
### Funcionalidades

- Scraping de páginas de listagem e detalhe de anúncios na OLX
- Extração de specs (CPU/GPU/RAM/Storage) via regex, com IA (Groq/Ollama) como fallback
- Validação de anúncios via Pydantic (barra itens sem preço/link)
- Persistência local em SQLite (`olx.db`)
- Limpeza automática de anúncios vendidos/expirados
- Cálculo de score/ranking dos PCs com base em benchmarks de CPU/GPU/RAM/Storage
- Dashboard Streamlit para identificar oportunidades de flip

<!-- Env Variables -->
### Variáveis de Ambiente

Para rodar este projeto, copie `.env.example` para `.env` e preencha sua
chave da Groq e demais configurações necessárias.

<!-- Getting Started -->
## Getting Started

<!-- Prerequisites -->
### Pré-requisitos

Este projeto usa Python.

```bash
python --version
```

<!-- Installation -->
### Instalação

Clone o projeto

```bash
git clone https://github.com/jgabko/PC_Hunter.git
cd PC_Hunter
```

Instale as dependências

```bash
pip install -r requirements.txt
```

Configure as variáveis de ambiente

```bash
cp .env.example .env
```

<!-- Project Structure -->
## Estrutura do Projeto

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

## Notas de Migração

Referentes à última reorganização de módulos do projeto:

- Os módulos que antes ficavam soltos na raiz (`Persist.py`, `olx_detail_page.py`,
  `specs.py`, `specs_AI.py`, `schema.py`) agora vivem em pacotes (`persistence/`,
  `scraping/`, `processing/`, `schema/`), no mesmo espírito da separação de
  responsabilidades usada no projeto ImobData.
- `Persist.py` virou `persistence/persist.py` (nome de módulo em minúsculas,
  convenção PEP 8) — se você tinha scripts próprios importando `import Persist`,
  troque para `from persistence import persist`.
- O nome do arquivo do banco (`olx.db`) e a URL base de busca agora vêm de
  `config.py` / `.env`, em vez de estarem hardcoded em cada arquivo.

<!-- Roadmap -->
## Roadmap

* [x] Scraping de anúncios da OLX
* [x] Extração de specs via regex + fallback com IA
* [x] Persistência em SQLite e limpeza automática
* [x] Dashboard Streamlit com ranking de oportunidades
<!--* [ ] Notificações automáticas de novas oportunidades
* [ ] Suporte a outras plataformas além da OLX-->

<!-- License -->
## Licença

Distribuído sem licença definida. Veja LICENSE.txt para mais informações.
