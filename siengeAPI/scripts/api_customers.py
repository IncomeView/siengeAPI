import time, traceback, pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
from db_utils import save_dataframe
from api_utils import fetch_limt200
from config import SIENGE_USERNAME, SIENGE_PASSWORD, POSTGRES_SCHEMA

BASE_URL = "https://api.sienge.com.br/olimpo/public/api/v1/customers"

def log_message(module: str, message: str):
    timestamp = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{module}] {message}", flush=True)

def normalize_customers(df):
    df = df.copy()
    # --- PHONES ---
    df = df.explode("phones").reset_index(drop=True)
    df["phones"] = df["phones"].apply(lambda x: x if isinstance(x, dict) else {})
    phones_df = pd.json_normalize(df["phones"]).add_prefix("phone_")
    df_1 = pd.concat([df.reset_index(drop=True), phones_df.reset_index(drop=True)], axis=1)
    df_1 = df_1.drop_duplicates(subset=["id"]).reset_index(drop=True)
    # --- ADDRESSES ---
    df = df_1.explode("addresses").reset_index(drop=True)
    df["addresses"] = df["addresses"].apply(lambda x: x if isinstance(x, dict) else {})
    addresses_df = pd.json_normalize(df["addresses"])
    df_2 = pd.concat([df.reset_index(drop=True), addresses_df.reset_index(drop=True)], axis=1)
    df_2 = df_2.drop_duplicates(subset=["id"]).reset_index(drop=True)
    # --- SPOUSE ---
    df = df_2.copy()
    df["spouse"] = df["spouse"].apply(lambda x: x if isinstance(x, dict) else {})
    spouse_df = pd.json_normalize(df["spouse"])[
        ["cpf", "name", "email", "sex", "birthDate", "cellphoneNumber"]
    ].add_prefix("spouse_")
    df_3 = pd.concat([df, spouse_df], axis=1)

    # familyIncome
    df_3["familyIncome"] = df_3["familyIncome"].apply(
        lambda x: ",".join(map(str, x)) if isinstance(x, list) else x
    )
    cols = [
        "id","name","cpf","cnpj","numberIdentityCard","foreigner","personType","sex","nationality","birthDate","profession","civilStatus","matrimonialRegime","email",
        "phone_type","phone_idd","phone_number","phone_note","createdAt","mailingAddress","type","streetName","number","complement","neighborhood","city","state","zipCode",
        "spouse_name","spouse_cpf","spouse_sex","spouse_birthDate","spouse_email","spouse_cellphoneNumber","familyIncome"
    ]
    return df_3.filter(items=cols)

def main():
    global_start = time.time()
    started_at = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%Y-%m-%d %H:%M:%S")
    try:
        df_raw = fetch_limt200(BASE_URL, SIENGE_USERNAME, SIENGE_PASSWORD)
        df_final = normalize_customers(df_raw)

        if df_final.empty:
            log_message("sienge_customers", "❌ Nenhum dado processado para clientes.")
            return
        df_final["upDate"] = datetime.now(ZoneInfo("America/Sao_Paulo"))
        # --- Salva Parquet localmente ---
        parquet_path = "/scripts/JSON/customers.parquet"
        df_final.to_parquet(parquet_path, index=False)
        log_message("customers", f"💾 Parquet salvo em: {parquet_path} ({len(df_final)} linhas)")
        # --- Salva no banco ---
        save_dataframe(df_final, "Customers", POSTGRES_SCHEMA)

        # --- Resumo final ---
        elapsed = time.time() - global_start
        log_message("sienge_customers", "Resumo da execução:")
        log_message(
            "sienge_customers",
            f"Customers - status: ✅ ok - início: {started_at} - tempo total: {elapsed:.2f}s - linhas: {len(df_final)}")
    except Exception as e:
        elapsed = time.time() - global_start
        log_message("sienge_customers", f"❌ Erro ao processar clientes após {elapsed:.2f}s: {e}")
        log_message("sienge_customers", traceback.format_exc())

if __name__ == "__main__":
    main()
