import requests
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
from config import SIENGE_USERNAME, SIENGE_PASSWORD, POSTGRES_SCHEMA
from db_utils import save_dataframe

BASE_URL = "https://api.sienge.com.br/olimpo/public/api/v1/payment-categories"

def fetch_financialCategories():
    """Busca categorias financeiras da API Sienge."""
    try:
        response = requests.get(BASE_URL, auth=(SIENGE_USERNAME, SIENGE_PASSWORD), timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print("Erro na requisição:", e)
        return pd.DataFrame()

    try: dados = response.json()
    except Exception:
        print("Resposta não é JSON válido:", response.text)
        return pd.DataFrame()

    if not dados:
        print("API respondeu, mas não retornou dados.")
        return pd.DataFrame()
    return pd.DataFrame(dados)

def normalize_financialCategories(df):
    """Normaliza categorias financeiras, expandindo hierarquia apenas para tpConta = 'R - resultado id'."""
    if df.empty:
        return df
    id_map = dict(zip(df["id"].astype(str), df["name"]))
    expanded_rows = [_expand_row(r, id_map) for _, r in df[df["tpConta"] == "R"].iterrows()]
    return pd.DataFrame(expanded_rows)

def _expand_row(row, id_map):
    """Função auxiliar para expandir uma linha em níveis hierárquicos."""
    codigo = str(row["id"])
    niveis = [codigo[:i] for i in range(1, len(codigo)+1) if codigo[:i] in id_map]
    cols = {}
    for j, n in enumerate(niveis[:-1]):  # exclui o último (que é o próprio R)
        cols[f"id{j+1}"] = n
        cols[f"fc{j+1}"] = id_map[n]
    for c in row.index:
        if c == "name":
            cols["financialCategoryName"] = row[c]
        elif c == "id":
            cols["financialCategoryId"] = row[c]
        else:
            cols[c] = row[c]
    return cols

def main():
    df_raw = fetch_financialCategories()
    df_final = normalize_financialCategories(df_raw)

    if df_final.empty:
        print("Nenhum dado processado para categorias financeiras.")
        return
    df_final["upDate"] = datetime.now(ZoneInfo("America/Sao_Paulo"))
    save_dataframe(df_final, "FinancialCategories", POSTGRES_SCHEMA)

if __name__ == "__main__":
    main()