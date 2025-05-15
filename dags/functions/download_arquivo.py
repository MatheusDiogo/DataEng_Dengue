import requests

def download_arquivo(url, caminho_destino):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(caminho_destino, 'wb') as f:
            for chunk in r.iter_content(chunk_size=10000):
                if chunk:  # filtra chunks vazios
                    f.write(chunk)
