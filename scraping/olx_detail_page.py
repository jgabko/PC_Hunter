import re
from bs4 import BeautifulSoup
from curl_cffi import requests
from curl_cffi.requests.exceptions import RequestsException

# url='https://pr.olx.com.br/regiao-de-curitiba-e-paranagua/informatica/computadores-e-desktops/pc-gamer-seminovo-1459792232?lis=listing_no_category'


def getDetails(url):
    """
    Busca a página de detalhes de um anúncio e retorna um dict {label: valor}.

    CORREÇÃO: `labels` e `categorias` eram listas GLOBAIS no módulo original,
    nunca eram limpas entre chamadas. Como o retorno era `dict(zip(labels,
    categorias))`, cada novo anúncio "herdava" campos de anúncios anteriores
    que não possuíam aquele campo específico — corrompendo dados
    silenciosamente (ex: um anúncio sem "Cor" podia voltar com a "Cor" do
    anúncio anterior). Agora as listas são locais à função, então cada
    chamada começa do zero.
    """
    labels = []
    categorias = []

    try:
        response = requests.get(url, impersonate="chrome110", timeout=15)
    except RequestsException as e:
        print(f"  [ERRO REDE] Falha ao buscar detalhes de {url}: {e}")
        return {}

    if response.status_code != 200:
        print(f"  [AVISO] Status {response.status_code} ao buscar {url}")
        return {}

    soup = BeautifulSoup(response.text, 'html.parser')

    desc_div = soup.find('div', attrs={'id': 'description-title'})
    if desc_div:
        descricao = desc_div.text.strip()
        if descricao:
            labels.append('Descrição')
            categorias.append(descricao)

    details_div = soup.find('div', attrs={'id': 'details'})
    if details_div:
        detail_cell = details_div.find_all('div', attrs={'class': 'ad__sc-2h9gkk-0'})

        for cell in detail_cell:
            label_tag = cell.find('span', attrs={'class': re.compile(r'typo-overline')})
            if not label_tag:
                continue
            label = label_tag.text.strip()

            find_a = cell.find('a')
            if find_a:
                categoria_tag = cell.find('a', attrs={'class': re.compile(r'ad__sc')})
            else:
                categoria_tag = cell.find('span', attrs={'class': re.compile(r'ad__sc')})

            if not categoria_tag:
                continue

            labels.append(label)
            categorias.append(categoria_tag.text.strip())

    return dict(zip(labels, categorias))
