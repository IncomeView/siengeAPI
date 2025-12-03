import requests
import pandas as pd

def fetch_limt200(BASE_URL, SIENGE_USERNAME, SIENGE_PASSWORD, limit=200):
    """
    Busca dados de uma API Sienge com paginação.
    - base_url: endpoint da API (sem parâmetros de paginação)
    - username/password: credenciais de autenticação
    - limit: quantidade de registros por página
    Retorna um DataFrame com todos os registros.
    """
    all_data, offset = [], 0
    while True:
        url = f"{BASE_URL}?limit={limit}&offset={offset}"
        try:
            response = requests.get(url, auth=(SIENGE_USERNAME, SIENGE_PASSWORD), timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print("Erro na requisição:", e)
            break

        dados = response.json()
        results = dados.get("results", [])
        if not results:
            break
        all_data.extend(results)
        offset += limit
    print(f"Total de registros baixados: {len(all_data)}")
    return pd.DataFrame(all_data)
