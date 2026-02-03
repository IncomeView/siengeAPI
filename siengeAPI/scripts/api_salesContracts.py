import time, traceback, pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo

from db_utils import save_dataframe, get_engine
from api_utils import fetch_limt200
from config import SIENGE_USERNAME, SIENGE_PASSWORD, POSTGRES_SCHEMA

BASE_URL = "https://api.sienge.com.br/olimpo/public/api/v1/sales-contracts"

def log_message(module: str, message: str):
    timestamp = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{module}] {message}", flush=True)

# Normalização
    """ Recebe o DataFrame retornado por fetch_limt200. """
def normalize_salesContracts(df_raw: pd.DataFrame):
    start_time = time.time()
    if df_raw is None or df_raw.empty:
        return tuple(pd.DataFrame([]) for _ in range(6))

    base_sc = df_raw.copy()
    base_sc['creation_date'] = datetime.now(ZoneInfo("America/Sao_Paulo"))
    # salesContractCustomers
    sc_c = base_sc[['id', 'salesContractCustomers']].explode('salesContractCustomers')
    sc_c = sc_c.loc[lambda df: df['salesContractCustomers'].apply(lambda x: isinstance(x, dict))]
    sc_c = sc_c.rename(columns={"id": "salesContractsId"})
    salesContractCustomers = pd.json_normalize(sc_c['salesContractCustomers'])
    if not salesContractCustomers.empty:
        salesContractCustomers['salesContractsId'] = sc_c['salesContractsId'].values
    # salesContractUnits
    sc_u = base_sc[['id', 'salesContractUnits']].explode('salesContractUnits')
    sc_u = sc_u.loc[lambda df: df['salesContractUnits'].apply(lambda x: isinstance(x, dict))]
    sc_u = sc_u.rename(columns={"id": "salesContractsId"})
    salesContractUnits = pd.json_normalize(sc_u['salesContractUnits'])
    if not salesContractUnits.empty:
        salesContractUnits['salesContractsId'] = sc_u['salesContractsId'].values
    # salesContractPaymentConditions
    sc_pc = base_sc[['id', 'paymentConditions']].explode('paymentConditions')
    sc_pc = sc_pc.loc[lambda df: df['paymentConditions'].apply(lambda x: isinstance(x, dict))]
    sc_pc = sc_pc.rename(columns={"id": "salesContractsId"})
    salesContractPaymentConditions = pd.json_normalize(sc_pc['paymentConditions'])
    if not salesContractPaymentConditions.empty:
        salesContractPaymentConditions['salesContractsId'] = sc_pc['salesContractsId'].values
    # salesContractLinkedCommissions
    sc_lc = base_sc[['id', 'linkedCommissions']].explode('linkedCommissions')
    sc_lc = sc_lc.loc[lambda df: df['linkedCommissions'].apply(lambda x: isinstance(x, dict))]
    sc_lc = sc_lc.rename(columns={"id": "salesContractsId"})
    salesContractLinkedCommissions = pd.json_normalize(sc_lc['linkedCommissions'])
    if not salesContractLinkedCommissions.empty:
        salesContractLinkedCommissions['salesContractsId'] = sc_lc['salesContractsId'].values
    # salesContractLinks
    sc_l = base_sc[['id', 'links']].explode('links')
    sc_l = sc_l.loc[lambda df: df['links'].apply(lambda x: isinstance(x, dict))]
    sc_l = sc_l.rename(columns={"id": "salesContractsId"})
    salesContractLinks = pd.json_normalize(sc_l['links'])
    if not salesContractLinks.empty:
        salesContractLinks['salesContractsId'] = sc_l['salesContractsId'].values
    # ajustes finais
    salesContract = base_sc.drop(columns=['salesContractCustomers', 'salesContractUnits', 'paymentConditions', 'linkedCommissions', 'links'])
    elapsed = time.time() - start_time
    log_message("salesContracts", f"✅ Normalização: ok | Tempo: {elapsed:.2f}s")

    return (
        salesContract,
        salesContractCustomers,
        salesContractUnits,
        salesContractPaymentConditions,
        salesContractLinkedCommissions,
        salesContractLinks)

# Gravação para update DB
def save_salesContracts_tables(engine, dfs, module="salesContracts"):
    names = [
        "SalesContract",
        "SalesContractCustomers",
        "SalesContractUnits",
        "SalesContractPaymentConditions",
        "SalesContractLinkedCommissions",
        "SalesContractLinks"]

    resumo = []
    with engine.begin() as conn:
        for name, df in zip(names, dfs):
            start = time.time()
            started_at = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%Y-%m-%d %H:%M:%S")
            try:
                if isinstance(df, pd.DataFrame) and not df.empty:
                    save_dataframe(df, name, POSTGRES_SCHEMA)
                    elapsed = time.time() - start
                    log_message(module, f"{name} - status: ✅ ok - início: {started_at} - tempo: {elapsed:.2f}s - linhas: {len(df)}")
                    resumo.append({"table": name, "status": "✅ ok", "rows": len(df), "elapsed": elapsed})
                else:
                    elapsed = time.time() - start
                    log_message(module, f"{name} - status: ⚠️ vazio - início: {started_at} - tempo: {elapsed:.2f}s - linhas: 0")
                    resumo.append({"table": name, "status": "⚠️ vazio", "rows": 0, "elapsed": elapsed})
            except Exception as e:
                elapsed = time.time() - start
                log_message(module, f"❌ Erro ao salvar {name}: {e}")
                log_message(module, traceback.format_exc())
                resumo.append({"table": name, "status": "❌ erro", "rows": None, "elapsed": elapsed})
    return resumo

# Main
def main():
    global_start = time.time()
    started_at = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%Y-%m-%d %H:%M:%S")
    try:
        df_raw = fetch_limt200(BASE_URL, SIENGE_USERNAME, SIENGE_PASSWORD)

        if df_raw.empty:
            log_message("salesContracts", "❌ Nenhum dado processado para salesContracts.")
            return
        # Normaliza
        dfs = normalize_salesContracts(df_raw)
        engine = get_engine()
        resumo = save_salesContracts_tables(engine, dfs)

        # --- Resumo final ---
        elapsed = time.time() - global_start
        status_global = "✅ ok" if all(r["status"] == "✅ ok" for r in resumo) else "⚠️ parcial"
        linhas_total = sum(r["rows"] for r in resumo if r["rows"])
        log_message("salesContracts", "Resumo da execução consolidado salesContracts:")
        log_message("salesContracts",
            f"salesContracts - status: {status_global} - início: {started_at} - tempo total: {elapsed:.2f}s - linhas totais: {linhas_total}")

    except Exception as e:
        elapsed = time.time() - global_start
        log_message("salesContracts", f"❌ Erro ao processar incomsalesContractse após {elapsed:.2f}s: {e}")
        log_message("salesContracts", traceback.format_exc())

if __name__ == "__main__":
    main()