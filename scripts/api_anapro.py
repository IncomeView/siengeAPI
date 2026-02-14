import time, traceback, pandas as pd, requests
from datetime import datetime
from zoneinfo import ZoneInfo
from io import BytesIO
from db_utils import save_dataframe
from config import POSTGRES_SCHEMA

ANAPRO_URL = "https://anapro-vendas-views-api.azurewebsites.net/views"
ANAPRO_PARAMS = {
    "token": "IyJYziEqRsg1",
    "nome": "vwTabelaoUnidade",
    "subscription-key": "ce2cee0473a84f4dbec57ef38b0bb45c"}
ANAPRO_HEADERS = {"Authorization": "UksAO24kixbPPGFy0wqfT+fgn9TDOpg9Ws9krFC4nr/J9e3mIVQSBX0LspSu+l2CMHw4+ThdNrHehk5deJGwS8VisbsDrlaNifvr8BeSA+WxX1McY/T5NB3nNkS7Um8L"}

def log_message(module: str, message: str):
    timestamp = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{module}] {message}", flush=True)

def fetch_anapro_excel():
    response = requests.get(
        ANAPRO_URL,
        params=ANAPRO_PARAMS,
        headers=ANAPRO_HEADERS
    )
    response.raise_for_status()
    return pd.read_excel(BytesIO(response.content))

def normalize_anapro(df):
    return df.copy()

def main():
    global_start = time.time()
    started_at = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%Y-%m-%d %H:%M:%S")
    try:
        df_raw = fetch_anapro_excel()
        df_final = normalize_anapro(df_raw)
        if df_final.empty:
            log_message("anapro", "❌ Nenhum dado retornado da API Anapro.")
            return
        df_final["upDate"] = datetime.now(ZoneInfo("America/Sao_Paulo"))

        save_dataframe(df_final, "AnaproTabelaoUnidades", "sienge")

        elapsed = time.time() - global_start
        log_message("anapro", f"Execução concluída em {elapsed:.2f}s — linhas: {len(df_final)}")
    except Exception as e:
        elapsed = time.time() - global_start
        log_message("anapro", f"❌ Erro após {elapsed:.2f}s: {e}")
        log_message("anapro", traceback.format_exc())

if __name__ == "__main__":
    main()