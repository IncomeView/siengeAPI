import time, traceback
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo

from db_utils import save_dataframe, get_engine
from api_utils import fetch_limtFull
from config import SIENGE_USERNAME, SIENGE_PASSWORD, POSTGRES_SCHEMA

def log_message(module: str, message: str):
    timestamp = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{module}] {message}", flush=True)

# URL
def build_url(subdomain: str, start_date: str, end_date: str, selection_type: str) -> str:
    """Monta a URL income."""
    base = f"https://api.sienge.com.br/{subdomain}/public/api/bulk-data/v1/income"
    params = (f"?startDate={start_date}"f"&endDate={end_date}"f"&selectionType={selection_type}")
    return base + params

# Normalização
    """
    Recebe o DataFrame retornado por fetch_limtFull.
    Espera uma coluna 'data' contendo listas de registros.
    Retorna tuple de DataFrames normalizados.
    """
def normalize_income(df_raw: pd.DataFrame):
    start_time = time.time()
    timestamp = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%H:%M:%S")
    if df_raw is None or df_raw.empty:
        return tuple(pd.DataFrame([]) for _ in range(5))

    # Confere se 'data' existe; se não, nada a fazer
    if "data" not in df_raw.columns:
        log_message("income", "❌ JSON income não contém coluna 'data'.")
        return tuple(pd.DataFrame([]) for _ in range(5))

    base_IN = pd.json_normalize(df_raw['data']).copy()
    base_IN['creation_date'] = datetime.now(ZoneInfo("America/Sao_Paulo"))
    base_IN.insert(0, 'id_base_cr', range(1,  len(base_IN) + 1))
    # Higienização
    for c in ["documentIdentificationId", "mainUnit", "documentNumber"]:
        if c in base_IN.columns:
            base_IN[c] = base_IN[c].astype(str).str.strip()
    base_IN = base_IN.rename(
        columns={
            "paymentTerm.id": "paymentTermid",
            "paymentTerm.descrition": "paymentTermdescrition"})    
    # receiptsCategories
    in_rc = base_IN[['id_base_cr', 'receiptsCategories']].explode('receiptsCategories')
    in_rc = in_rc.loc[lambda df: df['receiptsCategories'].apply(lambda x: isinstance(x, dict))]
    receiptsCategories = pd.json_normalize(in_rc['receiptsCategories'])
    if not receiptsCategories.empty:
        receiptsCategories['id_base_cr'] = in_rc['id_base_cr'].values
    # receipts
    in_r = base_IN[['id_base_cr', 'receipts']].explode('receipts')
    in_r = in_r.loc[lambda df: df['receipts'].apply(lambda x: isinstance(x, dict))]
    receipts = pd.json_normalize(in_r['receipts'])
    if not receipts.empty:
        receipts['id_base_cr'] = in_r['id_base_cr'].values
        receipts.insert(0, "id_base_cr_r", range(1, len(receipts) + 1))
    # bankMovements dentro de receipts
    in_r_bm = receipts[["id_base_cr_r", "id_base_cr", "bankMovements"]].explode("bankMovements")
    in_r_bm = in_r_bm.loc[in_r_bm["bankMovements"].apply(lambda x: isinstance(x, dict))]
    bankMovements_r = pd.json_normalize(in_r_bm["bankMovements"])
    if not bankMovements_r.empty:
        bankMovements_r["id_base_cr"] = in_r_bm["id_base_cr"].values
        bankMovements_r['id_base_cr_r'] = in_r_bm['id_base_cr_r'].values
    # financialCategories dentro de bankMovements/receipts
    in_r_bm_fc = bankMovements_r[["id_base_cr_r", "id_base_cr", "financialCategories"]].explode("financialCategories")
    in_r_bm_fc = in_r_bm_fc.loc[in_r_bm_fc["financialCategories"].apply(lambda x: isinstance(x, dict))]
    financialCategories = pd.json_normalize(in_r_bm_fc["financialCategories"])
    if not financialCategories.empty:
        financialCategories["id_base_cr"] = in_r_bm_fc["id_base_cr"].values
        financialCategories['id_base_cr_r'] = in_r_bm_fc['id_base_cr_r'].values

    # ajustes finais
    base_IN = base_IN.drop(columns=['receipts', 'receiptsCategories'])
    receipts = receipts.drop(columns=['bankMovements', 'creditDate'])
    bankMovements_r = bankMovements_r.drop(columns=['financialCategories'])
    elapsed = time.time() - start_time
    log_message("income", f"✅ Normalização: ok | Tempo: {elapsed:.2f}s")

    return (
        base_IN,
        receiptsCategories,
        receipts,
        bankMovements_r,
        financialCategories)

# Gravação para update DB
def save_income_tables(engine, dfs, module="income"):
    names = [
        "Income",
        "IncomeCategoriesReceipts",
        "IncomeReceipts",
        "IncomeReceiptsBankMovements",
        "IncomeReceiptsBankMovementsFinancialCategories"
    ]
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
            selection_type="D")
        # 2) Busca JSON e DataFrame bruto via api_utils
        df_raw = fetch_limtFull(
            BASE_URL=url,
            SIENGE_USERNAME=SIENGE_USERNAME,
            SIENGE_PASSWORD=SIENGE_PASSWORD,
            module="income",
            timeout=300
        )
        if df_raw.empty:
            log_message("income", "❌ Nenhum dado processado para income.")
            return
        # 3) Normaliza
        dfs = normalize_income(df_raw)
        # 3.1) Salva DataFrames finais localmente em Parquet
        df_names = [
            "Income",
            "IncomeCategoriesReceipts",
            "IncomeReceipts",
            "IncomeReceiptsBankMovements",
            "IncomeReceiptsBankMovementsFinancialCategories"
        ]
        for name, df in zip(df_names, dfs):
            if isinstance(df, pd.DataFrame) and not df.empty:
                df.to_parquet(f"/scripts/JSON/{name}.parquet", index=False)
                log_message("income", f"💾 Arquivo salvo: .parquet ({len(df)} linhas)")
            else:
                log_message("income", f"⚠️ DataFrame vazio, não salvo: {name}")
        # 4) Salva no banco
        log_message("income", "🔗 Início do upload para os dataframes income")
        engine = get_engine()
        resumo = save_income_tables(engine, dfs)
        # 5) Resumo
        elapsed = time.time() - global_start
        status_global = "✅ ok" if all(r["status"] == "✅ ok" for r in resumo) else "⚠️ parcial"
        linhas_total = sum(r["rows"] for r in resumo if r["rows"])
        log_message("income", "Resumo da execução consolidado income:")
        log_message("income",
            f"income - status: {status_global} - início: {started_at} - tempo total: {elapsed:.2f}s - linhas totais: {linhas_total}")

    except Exception as e:
        elapsed = time.time() - global_start
        log_message("income", f"❌ Erro ao processar income após {elapsed:.2f}s: {e}")
        log_message("income", traceback.format_exc())

if __name__ == "__main__":
    main()