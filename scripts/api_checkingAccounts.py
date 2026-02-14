import time, traceback, pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
from db_utils import save_dataframe_insert
from api_utils import fetch_limt200
from config import SIENGE_USERNAME, SIENGE_PASSWORD, POSTGRES_SCHEMA

BASE_URL = "https://api.sienge.com.br/olimpo/public/api/v1/checking-accounts"

def log_message(module: str, message: str):
    timestamp = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{module}] {message}", flush=True)

def normalize_checkingAccounts(df):
    df = df.copy()
    df["id"] = df["companyId"].astype(str) + "_" + df["accountNumber"].astype(str)
    df.insert(0, "id", df.pop("id"))
    df = df.drop_duplicates(subset=["id"])

    if "accountType" not in df.columns:
        return df
    at = df[['id', 'accountType']].copy()
    at = at[at['accountType'].apply(lambda x: isinstance(x, dict))]
    if at.empty:
        return df.drop(columns=['accountType'])
    at_norm = pd.json_normalize(at['accountType'])
    at_norm = at_norm.rename(columns={"id": "accountTypeId","description": "accountTypeDescription"})
    at_norm['id'] = at['id'].values
    df = df.merge(at_norm, on='id', how='left')
    df = df.drop(columns=['accountType'])
    return df

def main():
    global_start = time.time()
    started_at = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%Y-%m-%d %H:%M:%S")
    try:
        df_raw = fetch_limt200(BASE_URL, SIENGE_USERNAME, SIENGE_PASSWORD)
        df_final = normalize_checkingAccounts(df_raw)

        if df_final.empty:
            log_message("checkingAccounts", "❌ Nenhum dado processado para clientes.")
            return
        df_final["upDate"] = datetime.now(ZoneInfo("America/Sao_Paulo"))
        save_dataframe_insert(df_final, "CheckingAccounts", POSTGRES_SCHEMA)

        # --- Resumo final ---
        elapsed = time.time() - global_start
        log_message("checkingAccounts", "Resumo da execução:")
        log_message(
            "checkingAccounts",
            f"checkingAccounts - status: ✅ ok - início: {started_at} - tempo total: {elapsed:.2f}s - linhas: {len(df_final)}")
    except Exception as e:
        elapsed = time.time() - global_start
        log_message("checkingAccounts", f"❌ Erro ao processar clientes após {elapsed:.2f}s: {e}")
        log_message("checkingAccounts", traceback.format_exc())

if __name__ == "__main__":
    main()
