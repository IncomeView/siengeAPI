import time, traceback
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from db_utils import save_dataframe, get_engine
from api_utils import fetch_limtFull
from config import SIENGE_USERNAME, SIENGE_PASSWORD, POSTGRES_SCHEMA

def log_message(module: str, message: str):
    timestamp = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{module}] {message}", flush=True)

# URL
def build_url(subdomain: str, start_date: str, end_date: str, selection_type: str, correction_indexer_id: int, correction_date: str,
              with_authorizations: bool, with_bank_movements: bool) -> str:
    """Monta a URL Outcome."""
    base = f"https://api.sienge.com.br/{subdomain}/public/api/bulk-data/v1/outcome"
    params = (
        f"?startDate={start_date}"f"&endDate={end_date}"f"&selectionType={selection_type}"f"&correctionIndexerId={correction_indexer_id}"
        f"&correctionDate={correction_date}"f"&withAuthorizations={'true' if with_authorizations else 'false'}"f"&withBankMovements={'true' if with_bank_movements else 'false'}")
    return base + params

# Normalização
    """
    Recebe o DataFrame retornado por fetch_limtFull.
    Espera uma coluna 'data' contendo listas de registros.
    Retorna tuple de DataFrames normalizados.
    """
def normalize_outcome(df_raw: pd.DataFrame):
    log_message("Outcome", "Normalização inciada...")
    if df_raw is None or df_raw.empty:
        return tuple(pd.DataFrame([]) for _ in range(8))

    # Confere se 'data' existe; se não, nada a fazer
    if "data" not in df_raw.columns:
        log_message("outcome", "❌ JSON Outcome não contém coluna 'data'.")
        return tuple(pd.DataFrame([]) for _ in range(8))
    # Normaliza o conteúdo de 'data' para colunas
    base_OC = pd.json_normalize(df_raw["data"]).copy()
    base_OC["creation_date"] = datetime.now(ZoneInfo("America/Sao_Paulo"))
    base_OC.insert(0, "id_Base_oc", range(1, len(base_OC) + 1))
    # Higienização
    for c in ["documentIdentificationId", "documentNumber"]:
        if c in base_OC.columns:
            base_OC[c] = base_OC[c].astype(str).str.strip()
    # paymentsCategories
    oc_pc = base_OC[["id_Base_oc", "paymentsCategories"]].explode("paymentsCategories")
    oc_pc = oc_pc.loc[oc_pc["paymentsCategories"].apply(lambda x: isinstance(x, dict))]
    paymentsCategories = pd.json_normalize(oc_pc["paymentsCategories"])
    if not paymentsCategories.empty:
        paymentsCategories["id_Base_oc"] = oc_pc["id_Base_oc"].values
    # authorizations
    oc_atz = base_OC[["id_Base_oc", "authorizations"]].explode("authorizations")
    oc_atz = oc_atz.loc[oc_atz["authorizations"].apply(lambda x: isinstance(x, dict))]
    authorizations = pd.json_normalize(oc_atz["authorizations"])
    if not authorizations.empty:
        authorizations["id_Base_oc"] = oc_atz["id_Base_oc"].values
    # departamentsCosts
    oc_dc = base_OC[["id_Base_oc", "departamentsCosts"]].explode("departamentsCosts")
    oc_dc = oc_dc.loc[oc_dc["departamentsCosts"].apply(lambda x: isinstance(x, dict))]
    departamentsCosts = pd.json_normalize(oc_dc["departamentsCosts"])
    if not departamentsCosts.empty:
        departamentsCosts["id_Base_oc"] = oc_dc["id_Base_oc"].values
    # buildingsCosts
    oc_bc = base_OC[["id_Base_oc", "buildingsCosts"]].explode("buildingsCosts")
    oc_bc = oc_bc.loc[oc_bc["buildingsCosts"].apply(lambda x: isinstance(x, dict))]
    buildingsCosts = pd.json_normalize(oc_bc["buildingsCosts"])
    if not buildingsCosts.empty:
        buildingsCosts["id_Base_oc"] = oc_bc["id_Base_oc"].values
    # payments
    oc_p = base_OC[["id_Base_oc", "payments"]].explode("payments")
    oc_p = oc_p.loc[oc_p["payments"].apply(lambda x: isinstance(x, dict))]
    payments = pd.json_normalize(oc_p["payments"])
    if not payments.empty:
        payments["id_Base_oc"] = oc_p["id_Base_oc"].values
        payments.insert(0, "id_Base_oc_p", range(1, len(payments) + 1))
    # bankMovements dentro de payments
    oc_p_bm = payments[["id_Base_oc_p", "id_Base_oc", "bankMovements"]].explode("bankMovements")
    oc_p_bm = oc_p_bm.loc[oc_p_bm["bankMovements"].apply(lambda x: isinstance(x, dict))]
    bankMovements = pd.json_normalize(oc_p_bm["bankMovements"])
    if not bankMovements.empty:
        bankMovements["id_Base_oc_p"] = oc_p_bm["id_Base_oc_p"].values
    # paymentCategories dentro de bankMovements
    oc_p_bm_pc = bankMovements[["id_Base_oc_p", "paymentCategories"]].explode("paymentCategories")
    oc_p_bm_pc = oc_p_bm_pc.loc[oc_p_bm_pc["paymentCategories"].apply(lambda x: isinstance(x, dict))]
    paymentCategories_bm = pd.json_normalize(oc_p_bm_pc["paymentCategories"])
    if not paymentCategories_bm.empty:
        paymentCategories_bm["id_Base_oc_p"] = oc_p_bm_pc["id_Base_oc_p"].values

    # ajustes finais
    base_OC = base_OC.drop(columns=["paymentsCategories", "departamentsCosts", "buildingsCosts", "payments", "authorizations"],errors="ignore")
    for col in ["originalAmount", "discountAmount", "taxAmount", "balanceAmount", "correctedBalanceAmount"]:
        if col in base_OC.columns:
            base_OC[col] = pd.to_numeric(base_OC[col], errors="coerce").fillna(0)
    for col in ["dueDate", "issueDate", "installmentBaseDate", "billDate"]:
        if col in base_OC.columns:
            base_OC[col] = pd.to_datetime(base_OC[col], errors="coerce").dt.date
    payments = payments.drop(columns=["bankMovements"], errors="ignore")
    bankMovements = bankMovements.drop(columns=["paymentCategories"], errors="ignore")
    for col in ["grossAmount", "monetaryCorrectionAmount", "interestAmount", "fineAmount", "discountAmount", "taxAmount", "netAmount"]:
        if col in payments.columns:
            payments[col] = pd.to_numeric(payments[col], errors="coerce").fillna(0)
    for col in ["calculationDate", "paymentDate"]:
        if col in payments.columns:
            payments[col] = pd.to_datetime(payments[col], errors="coerce").dt.date

    return (
        base_OC,
        paymentsCategories,
        authorizations,
        departamentsCosts,
        buildingsCosts,
        payments,
        bankMovements,
        paymentCategories_bm,
    )

# Gravação para update DB
def save_outcome_tables(engine, dfs, module="outcome"):
    names = [
        "Outcome",
        "OutcomeCategoriesPayments",
        "OutcomeAuthorizations",
        "OutcomeDepartamentsCosts",
        "OutcomeBuildingsCosts",
        "OutcomePayments",
        "OutcomePaymentsBankMovements",
        "OutcomePaymentsBankMovementsPaymentsCategories"]

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
        # 1) URL
        url = build_url(
            subdomain="olimpo",
            start_date="2014-01-01",
            end_date="2065-01-01",
            selection_type="D",
            correction_indexer_id=0,
            correction_date=(datetime.now(ZoneInfo("America/Sao_Paulo")) + timedelta(days=30)).strftime("%Y-%m-%d"),
            with_authorizations=True,
            with_bank_movements=True)

        # 2) Busca JSON e DataFrame bruto via api_utils
        df_raw = fetch_limtFull(BASE_URL=url, SIENGE_USERNAME=SIENGE_USERNAME, SIENGE_PASSWORD=SIENGE_PASSWORD, 
                                module="outcome", timeout=300)                                                              #, json_path_env="JSON_PATH_OUTCOME"
        if df_raw.empty:
            log_message("outcome", "❌ Nenhum dado processado para Outcome.")
            return
        # 3) Normaliza
        dfs = normalize_outcome(df_raw)
        engine = get_engine()
        resumo = save_outcome_tables(engine, dfs)

        # 5) Resumo
        elapsed = time.time() - global_start
        status_global = "✅ ok" if all(r["status"] == "✅ ok" for r in resumo) else "⚠️ parcial"
        linhas_total = sum(r["rows"] for r in resumo if r["rows"])
        log_message("outcome", "Resumo da execução consolidado outcome:")
        log_message("outcome",
            f"Outcome - status: {status_global} - início: {started_at} - tempo total: {elapsed:.2f}s - linhas totais: {linhas_total}")

    except Exception as e:
        elapsed = time.time() - global_start
        log_message("outcome", f"❌ Erro ao processar Outcome após {elapsed:.2f}s: {e}")
        log_message("outcome", traceback.format_exc())

if __name__ == "__main__":
    main()