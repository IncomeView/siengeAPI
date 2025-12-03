import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
from config import SIENGE_USERNAME, SIENGE_PASSWORD, POSTGRES_SCHEMA
from db_utils import save_dataframe
from api_utils import fetch_limt200

BASE_URL = "https://api.sienge.com.br/olimpo/public/api/v1/customers"

def normalize_customers(df):
    """Normaliza os campos aninhados (phones, addresses, spouse)."""
    # phones
    df = df.explode("phones").reset_index(drop=True)
    df = df.drop_duplicates(subset=["id"]).reset_index(drop=True)
    phones_df = pd.json_normalize(df["phones"]).add_prefix("phone_")
    phones_df = phones_df.loc[df.index].reset_index(drop=True)
    df_1 = pd.concat([df, phones_df], axis=1)
    # addresses
    df = df_1.explode("addresses").reset_index(drop=True)
    df = df.drop_duplicates(subset=["id"]).reset_index(drop=True)
    addresses_df = pd.json_normalize(df["addresses"])
    addresses_df = addresses_df.loc[df.index].reset_index(drop=True)
    df_2 = pd.concat([df, addresses_df], axis=1)
    # spouse
    df = df_2.copy()
    spouse = df["spouse"].apply(lambda x: x if isinstance(x, dict) else {})
    spouse_df = pd.json_normalize(spouse)[["cpf", "name", "email", "sex", "birthDate", "cellphoneNumber"]].add_prefix("spouse_")
    df_3 = pd.concat([df, spouse_df], axis=1)

    df_3["familyIncome"] = df_3["familyIncome"].apply(lambda x: ",".join(map(str, x)) if isinstance(x, list) else x)
    cols =["id","name","cpf","cnpj","numberIdentityCard","foreigner","personType","sex","nationality","birthDate","profession","civilStatus","matrimonialRegime","email",
        "phone_type","phone_idd","phone_number","phone_note","createdAt","mailingAddress","type","streetName","number","complement","neighborhood","city","state","zipCode",
        "spouse_name","spouse_cpf","spouse_sex","spouse_birthDate","spouse_email","spouse_cellphoneNumber","familyIncome"]
    df = df_3.filter(items=cols)
    return df

def main():
    df_raw = fetch_limt200(BASE_URL, SIENGE_USERNAME, SIENGE_PASSWORD)
    df_final = normalize_customers(df_raw)
    df_final["upDate"] = datetime.now(ZoneInfo("America/Sao_Paulo"))
    save_dataframe(df_final, "Customers", POSTGRES_SCHEMA)

if __name__ == "__main__":
    main()
