import time, traceback, pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
from db_utils import save_dataframe
from api_utils import fetch_limt200
from config import SIENGE_USERNAME, SIENGE_PASSWORD, POSTGRES_SCHEMA

BASE_URL = "https://api.sienge.com.br/olimpo/public/api/v1/creditors"

def log_message(module: str, message: str):
    timestamp = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{module}] {message}", flush=True)

def normalize_creditors(df):
    df = df.copy()
    df = df.rename(columns={"id": "creditorsId"})

    ad = df[['creditorsId', 'address']].copy()
    ad = ad[ad['address'].apply(lambda x: isinstance(x, dict))]
    ad_norm = pd.json_normalize(ad['address'])
    ad_norm = ad_norm.rename(columns={
        "cityId": "addressCityId",
        "cityName": "addressCityName",
        "streetName": "addressStreetName",
        "number": "addressNumber",
        "complement": "addressComplement",
        "neighborhood": "addressNeighborhood",
        "state": "addressState",
        "zipCode": "addressZipCode"})
    ad_norm['creditorsId'] = ad['creditorsId'].values
    df = df.merge(ad_norm, on='creditorsId', how='left')

    # phones
    # phones ddd e number
    ph = df[['creditorsId', 'phones']].copy()
    # garante lista e extrai apenas dicts válidos
    ph['phones'] = ph['phones'].apply(lambda x: x if isinstance(x, list) else [])
    ph['phones'] = ph['phones'].apply(lambda lst: [p for p in lst if isinstance(p, dict)])
    # remove duplicados por ddd+number
    ph['phones'] = ph['phones'].apply(lambda lst: list({(p.get('ddd'), p.get('number')): p for p in lst}.values()))
    # limita a 3 telefones
    ph['phones'] = ph['phones'].apply(lambda lst: lst[:3])
    # cria colunas vazias
    for i in range(1, 4):
        df[f'phonesddd{i}'] = None
        df[f'phonesNumber{i}'] = None
    # preenche colunas
    for idx, row in ph.iterrows():
        phones = row['phones']
        for i, p in enumerate(phones, start=1):
            df.loc[df['creditorsId'] == row['creditorsId'], f'phonesddd{i}'] = p.get('ddd')
            df.loc[df['creditorsId'] == row['creditorsId'], f'phonesNumber{i}'] = p.get('number')
    # type e observation → somente do primeiro telefone
    df['phonesType'] = ph['phones'].apply(lambda lst: lst[0].get('type') if lst else None)
    df['phonesObservation'] = ph['phones'].apply(lambda lst: lst[0].get('observation') if lst else None)

    # contacts
    ct = df[['creditorsId', 'contacts']].copy()
    ct['contacts'] = ct['contacts'].apply(lambda x: x if isinstance(x, list) else [])
    ct['contacts'] = ct['contacts'].apply(lambda lst: [c for c in lst if isinstance(c, dict)])
    # cria colunas vazias
    df['contactsName'] = None
    df['contactsddd'] = None
    df['contactsNumber'] = None
    df['contactsExtension'] = None
    df['contactsSkype'] = None
    df['contactsMsn'] = None
    df['contactsEmail1'] = None
    df['contactsEmail2'] = None
    # percorre cada creditorId
    for idx, row in ct.iterrows():
        creditorId = row['creditorsId']
        contacts = row['contacts']
        if not contacts:
            continue
        # 1º contatos
        first = contacts[0]
        df.loc[df['creditorsId'] == creditorId, 'contactsName'] = first.get('name')
        df.loc[df['creditorsId'] == creditorId, 'contactsddd'] = first.get('ddd')
        df.loc[df['creditorsId'] == creditorId, 'contactsNumber'] = first.get('number')
        df.loc[df['creditorsId'] == creditorId, 'contactsExtension'] = first.get('extension')
        df.loc[df['creditorsId'] == creditorId, 'contactsSkype'] = first.get('skype')
        df.loc[df['creditorsId'] == creditorId, 'contactsMsn'] = first.get('msn')
        # EMAILS → coletar todos, deduplicar, limitar a 2
        emails = []
        for c in contacts:
            if isinstance(c.get('email'), str):
                emails.append(c['email'])
        # remove duplicados mantendo ordem
        emails = list(dict.fromkeys(emails))
        # limita a 2
        emails = emails[:2]
        if len(emails) >= 1:
            df.loc[df['creditorsId'] == creditorId, 'contactsEmail1'] = emails[0]
        if len(emails) >= 2:
            df.loc[df['creditorsId'] == creditorId, 'contactsEmail2'] = emails[1]

    # links
    lk = df[['creditorsId', 'links']].explode('links')
    lk = lk[lk['links'].apply(lambda x: isinstance(x, dict))]
    lk_norm = pd.json_normalize(lk['links'])
    lk_norm = lk_norm.rename(columns={
        "rel": "linksRel",
        "href": "linksHref"})
    lk_norm['creditorsId'] = lk['creditorsId'].values
    df = df.merge(lk_norm, on='creditorsId', how='left')

    df = df.rename(columns={"creditorsId": "id"})
    df = df.drop(columns=['address', 'phones', 'emails', 'contacts', 'links', 'otherContactMethods'], errors='ignore')
    return df

def main():
    global_start = time.time()
    started_at = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%Y-%m-%d %H:%M:%S")
    try:
        df_raw = fetch_limt200(BASE_URL, SIENGE_USERNAME, SIENGE_PASSWORD)
        df_final = normalize_creditors(df_raw)

        if df_final.empty:
            log_message("creditors", "❌ Nenhum dado processado para clientes.")
            return
        df_final["upDate"] = datetime.now(ZoneInfo("America/Sao_Paulo"))
        # --- Salva Parquet localmente ---
        parquet_path = "/scripts/JSON/creditors.parquet"
        df_final.to_parquet(parquet_path, index=False)
        log_message("creditors", f"💾 Parquet salvo em: {parquet_path} ({len(df_final)} linhas)")
        # --- Salva no banco ---
        save_dataframe(df_final, "Creditors", POSTGRES_SCHEMA)

        # --- Resumo final ---
        elapsed = time.time() - global_start
        log_message("creditors", "Resumo da execução:")
        log_message(
            "creditors",
            f"creditors - status: ✅ ok - início: {started_at} - tempo total: {elapsed:.2f}s - linhas: {len(df_final)}")
    except Exception as e:
        elapsed = time.time() - global_start
        log_message("creditors", f"❌ Erro ao processar clientes após {elapsed:.2f}s: {e}")
        log_message("creditors", traceback.format_exc())

if __name__ == "__main__":
    main()
