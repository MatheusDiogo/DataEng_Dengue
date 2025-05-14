import requests
from bs4 import BeautifulSoup
import os
from functions.enviar_email import enviar_email

def verificar_atualizacao(url = 'https://opendatasus.saude.gov.br/dataset/arboviroses-dengue/resource/5c9132a9-77c2-4b15-8afc-a43c58fc9ec0'):
    # Requisição HTTP
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    arquivo_data='/opt/airflow/data/ultima_data.txt'

    soup = BeautifulSoup(response.content, "html.parser")

    # Encontra todas as linhas da tabela
    linhas = soup.find_all("tr")

    data_atual_site = None

    for linha in linhas:
        th = linha.find("th")
        if th and "Dados atualizados pela última vez" in th.get_text():
            td = linha.find("td")
            if td:
                data_atual_site = td.get_text(strip=True)
            break

    if data_atual_site is None:
        enviar_email("Não foi possível encontrar a data de atualização no site. Favor verificar no Site se houve alguma mudança!", "matheusdiogoeng@gmail.com") #E Email deveria ser colocado em uma variável de ambiente para não expor no github, também seria necessário criar a lista de emails em cópia
        raise ValueError("Não foi possível encontrar a data de atualização no site.")

    # Verificar se o arquivo existe
    if os.path.exists(arquivo_data):
        with open(arquivo_data, 'r', encoding='utf-8') as f:
            data_salva = f.read().strip()
    else:
        data_salva = ''

    print("Ultima atualização no site:", data_atual_site)
    print("Ultima atualização local:", data_salva)
        
    # Comparar datas
    if data_atual_site > data_salva:
        # Atualizou -> salvar nova data e retornar True
        with open(arquivo_data, 'w', encoding='utf-8') as f:
            f.write(data_atual_site)

        print("Os dados foram atualizados.")
        enviar_email("Os dados foram atualizados!", "matheusdiogoeng@gmail.com") #E Email deveria ser colocado em uma variável de ambiente para não expor no github, também seria necessário criar a lista de emails em cópia
        return True
    else:
        # Não atualizou
        print("Os dados não mudaram desde a última verificação.")
        return False