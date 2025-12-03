import requests
import pandas as pd
from config import SIENGE_USERNAME, SIENGE_PASSWORD

def get_financialCategories():
    url = "https://api.sienge.com.br/olimpo/public/api/v1/payment-categories"
    response = requests.get(url, auth=(SIENGE_USERNAME, SIENGE_PASSWORD))

    if response.status_code == 200:
        try:
            dados = response.json()
        except Exception:
            print("Resposta não é JSON válido:", response.text)
            return None

        if not dados:
            print("API respondeu, mas não retornou dados.")
            return None
        df = pd.DataFrame(dados)

        # aplica transformação apenas para tpConta = 'R'
        id_map = dict(zip(df["id"].astype(str), df["name"]))
        df_out = pd.DataFrame([
            _expand_row(r, id_map) for _, r in df[df["tpConta"] == "R"].iterrows()])
        return df_out
    else:
        print("Erro ao acessar API:", response.status_code, response.text)
        return None

    """Função auxiliar interna para expandir uma linha."""
def _expand_row(row, id_map):
    codigo = str(row["id"])
    niveis = [codigo[:i] for i in range(1, len(codigo)+1) if codigo[:i] in id_map]
    cols = {}

    for j, n in enumerate(niveis[:-1]):  # exclui o último (que é o próprio R)
        cols[f"id{j+1}"] = n
        cols[f"fc{j+1}"] = id_map[n]
    for c in row.index:
        if c == "name":
            cols["financialCategoryName"] = row[c]
        if c == "id":
            cols["financialCategoryId"] = row[c]
        else:
            cols[c] = row[c]
    return cols