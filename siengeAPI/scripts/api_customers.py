import pandas as pd
from config import SIENGE_USERNAME, SIENGE_PASSWORD, POSTGRES_SCHEMA
from db_utils import save_dataframe
from api_utils import fetch_limt200

BASE_URL = "https://api.sienge.com.br/olimpo/public/api/v1/customers"

def normalize_customers(df):
    """Normaliza os campos aninhados (phones, addresses, spouse)."""
    # phones
    df_phones = df.explode("phones").reset_index(drop=True)
    phones_df = pd.json_normalize(df_phones["phones"]).add_prefix("phone_")
    df = pd.concat([df_phones, phones_df], axis=1)
    # addresses
    df_addr = df.explode("addresses").reset_index(drop=True)
    addresses_df = pd.json_normalize(df_addr["addresses"])
    df = pd.concat([df_addr, addresses_df], axis=1)
    # spouse
    spouse = df["spouse"].apply(lambda x: x if isinstance(x, dict) else {})
    spouse_df = pd.json_normalize(spouse)[["cpf","name","email","sex","birthDate","cellphoneNumber"]].add_prefix("spouse_")
    df = pd.concat([df, spouse_df], axis=1)
    return df

def main():
    df_raw = fetch_limt200(BASE_URL, SIENGE_USERNAME, SIENGE_PASSWORD)
    df_final = normalize_customers(df_raw)
    save_dataframe(df_final, "customers", POSTGRES_SCHEMA)

if __name__ == "__main__":
    main()
