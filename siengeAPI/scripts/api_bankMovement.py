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
def build_url(subdomain: str, start_date: str, end_date: str) -> str:
    """Monta a URL bankMovement."""
    base = f"https://api.sienge.com.br/{subdomain}/public/api/bulk-data/v1/bank-movement"
    params = (f"?startDate={start_date}"f"&endDate={end_date}")
    return base + params

# Normalização
    """
    Recebe o DataFrame retornado por fetch_limtFull.
    Espera uma coluna 'data' contendo listas de registros.
    Retorna tuple de DataFrames normalizados.
    """
def normalize_bankMovement(df_raw: pd.DataFrame):
    log_message("bankMovement", "Normalização inciada...")
    if df_raw is None or df_raw.empty:
        return tuple(pd.DataFrame([]) for _ in range(4))

    # Confere se 'data' existe; se não, nada a fazer
    if "data" not in df_raw.columns:
        log_message("bankMovement", "❌ JSON bankMovement não contém coluna 'data'.")
        return tuple(pd.DataFrame([]) for _ in range(4))

    base_BM = pd.json_normalize(df_raw['data']).copy()
    base_BM['creation_date'] = datetime.now(ZoneInfo("America/Sao_Paulo"))
    base_BM.insert(0, 'id_Base_bm', range(1,  len(base_BM) + 1))
    # Higienização
    for c in ["documentIdentificationId"]:
        if c in base_BM.columns:
            base_BM[c] = base_BM[c].astype(str).str.strip()
    # financialCategories
    bm_fc = base_BM[['id_Base_bm', 'financialCategories']].explode('financialCategories')
    bm_fc = bm_fc.loc[lambda df: df['financialCategories'].apply(lambda x: isinstance(x, dict))]
    financialCategories = pd.json_normalize(bm_fc['financialCategories'])
    if not financialCategories.empty:
        financialCategories['id_Base_bm'] = bm_fc['id_Base_bm'].values
    # departamentCosts
    bm_dc = base_BM[['id_Base_bm', 'departamentCosts']].explode('departamentCosts')
    bm_dc = bm_dc.loc[lambda df: df['departamentCosts'].apply(lambda x: isinstance(x, dict))]
    departamentCosts = pd.json_normalize(bm_dc['departamentCosts'])
    if not departamentCosts.empty:
        departamentCosts['id_Base_bm'] = bm_dc['id_Base_bm'].values
    # buldingCosts
    bm_bc = base_BM[['id_Base_bm', 'buldingCosts']].explode('buldingCosts')
    bm_bc = bm_bc.loc[lambda df: df['buldingCosts'].apply(lambda x: isinstance(x, dict))]
    buldingCosts = pd.json_normalize(bm_bc['buldingCosts'])
    if not buldingCosts.empty:
        buldingCosts['id_Base_bm'] = bm_bc['id_Base_bm'].values

    # ajustes finais
    base_BM = base_BM.drop(columns=['financialCategories', 'departamentCosts', 'buldingCosts'])
    return (
        base_BM,
        financialCategories,
        departamentCosts,
        buldingCosts)

# Gravação para update DB
def save_bankMovement_tables(engine, dfs, module="bankMovement"):
    names = [
        "BankMovement",
        "BankMovementFinancialCategories",
        "BankMovementDepartamentCosts",
        "BankMovementBuldingCosts"]

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
            end_date=datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%Y-%m-%d"))
        # 2) Busca JSON e DataFrame bruto via api_utils
        df_raw = fetch_limtFull(
            BASE_URL=url,
            SIENGE_USERNAME=SIENGE_USERNAME,
            SIENGE_PASSWORD=SIENGE_PASSWORD,
            module="bankMovement",
            timeout=300
        )
        if df_raw.empty:
            log_message("bankMovement", "❌ Nenhum dado processado para bankMovement.")
            return
        # 3) Normaliza
        dfs = normalize_bankMovement(df_raw)
        # 3.1) Salva DataFrames finais localmente em Parquet
        df_names = [
            "bankMovement",
            "bankMovementFinancialCategories",
            "bankMovementDepartamentCosts",
            "bankMovementBuldingCosts"
        ]
        for name, df in zip(df_names, dfs):
            if isinstance(df, pd.DataFrame) and not df.empty:
                df.to_parquet(f"/scripts/JSON/{name}.parquet", index=False)
                log_message("bankMovement", f"💾 Arquivo salvo: .parquet ({len(df)} linhas)")
            else:
                log_message("bankMovement", f"⚠️ DataFrame vazio, não salvo: {name}")
        # 4) Salva no banco
        log_message("bankMovement", "🔗 Início do upload para os dataframes bankMovement")
        engine = get_engine()
        resumo = save_bankMovement_tables(engine, dfs)
        # 5) Resumo
        elapsed = time.time() - global_start
        status_global = "✅ ok" if all(r["status"] == "✅ ok" for r in resumo) else "⚠️ parcial"
        linhas_total = sum(r["rows"] for r in resumo if r["rows"])
        log_message("bankMovement", "Resumo da execução consolidado bankMovement:")
        log_message("bankMovement",
            f"bankMovement - status: {status_global} - início: {started_at} - tempo total: {elapsed:.2f}s - linhas totais: {linhas_total}")

    except Exception as e:
        elapsed = time.time() - global_start
        log_message("bankMovement", f"❌ Erro ao processar bankMovement após {elapsed:.2f}s: {e}")
        log_message("bankMovement", traceback.format_exc())

if __name__ == "__main__":
    main()