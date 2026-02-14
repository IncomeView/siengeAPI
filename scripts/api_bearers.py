import time, traceback, pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
from db_utils import save_dataframe
from api_utils import fetch_limt200
from config import SIENGE_USERNAME, SIENGE_PASSWORD, POSTGRES_SCHEMA

BASE_URL = "https://api.sienge.com.br/olimpo/public/api/v1/bearers-receivable"

def log_message(module: str, message: str):
    timestamp = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{module}] {message}", flush=True)

def normalize_bearers(df):
    return df.copy()

def main():
    global_start = time.time()
    started_at = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%Y-%m-%d %H:%M:%S")
    try:
        df_raw = fetch_limt200(BASE_URL, SIENGE_USERNAME, SIENGE_PASSWORD)
        df_final = normalize_bearers(df_raw)

        if df_final.empty:
            log_message("bearers", "❌ Nenhum dado processado para clientes.")
            return
        df_final["upDate"] = datetime.now(ZoneInfo("America/Sao_Paulo"))
        save_dataframe(df_final, "BearersReceivable", POSTGRES_SCHEMA)

        # --- Resumo final ---
        elapsed = time.time() - global_start
        log_message("bearers", "Resumo da execução:")
        log_message(
            "bearers",
            f"bearers - status: ✅ ok - início: {started_at} - tempo total: {elapsed:.2f}s - linhas: {len(df_final)}")
    except Exception as e:
        elapsed = time.time() - global_start
        log_message("bearers", f"❌ Erro ao processar clientes após {elapsed:.2f}s: {e}")
        log_message("bearers", traceback.format_exc())

if __name__ == "__main__":
    main()
