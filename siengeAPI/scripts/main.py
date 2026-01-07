import traceback, time, pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
from api_financialCategory import main as run_financial_category
from api_customers import main as run_customers
from api_outcome import main as run_outcome
from api_bankMovement import main as run_bankMovement
from api_income import main as run_income
from mvw_atualizacao import refresh_views as run_mvw
from api_businessUnits import main as run_bu


def log_message(module: str, message: str):
    timestamp = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{module}] {message}", flush=True)

def run_with_timing(module_name: str, func):
    """Executa uma função, loga checkpoints e tempo de execução."""
    start = time.time()
    started_at = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%Y-%m-%d %H:%M:%S")
    try:
        # executa a função principal
        result = func()
        elapsed = time.time() - start
        rows = None
        try:
            if isinstance(result, pd.DataFrame):
                rows = len(result)
        except Exception:
            pass
        return {"module": module_name, "status": "✅ ok", "elapsed": elapsed, "started_at": started_at, "rows": rows}
    except Exception as e:
        elapsed = time.time() - start
        log_message(module_name, f"❌ Erro após {elapsed:.2f}s: {e}")
        log_message(module_name, traceback.format_exc())
        return {"module": module_name, "status": "❌ erro", "elapsed": elapsed, "started_at": started_at, "rows": None}

def main():
    global_start = time.time()
    resumo = []
    # --- Executa financialCategory ---
    try:
        resumo.append(run_with_timing("financialCategory", run_financial_category))
    except Exception as e:
        elapsed = time.time() - global_start
        log_message("financialCategory", f"❌ Erro inesperado: {e}")
        resumo.append({"module": "financialCategory", "status": "❌ erro", "elapsed": elapsed, "started_at": None, "rows": None})
    # --- Executa customers ---
    try:
        resumo.append(run_with_timing("customers", run_customers))
    except Exception as e:
        elapsed = time.time() - global_start
        log_message("customers", f"❌ Erro inesperado: {e}")
        resumo.append({"module": "customers", "status": "❌ erro", "elapsed": elapsed, "started_at": None, "rows": None})
    # --- Executa outcome ---
    try:
        resumo.append(run_with_timing("outcome", run_outcome))
    except Exception as e:
        elapsed = time.time() - global_start
        log_message("outcome", f"❌ Erro inesperado: {e}")
        resumo.append({"module": "outcome", "status": "❌ erro", "elapsed": elapsed, "started_at": None, "rows": None})
    # --- Executa bankMovement ---
    try:
        resumo.append(run_with_timing("bankMovement", run_bankMovement))
    except Exception as e:
        elapsed = time.time() - global_start
        log_message("bankMovement", f"❌ Erro inesperado: {e}")
        resumo.append({"module": "bankMovement", "status": "❌ erro", "elapsed": elapsed, "started_at": None, "rows": None})
    # --- Executa income ---
    try:
        resumo.append(run_with_timing("income", run_income))
    except Exception as e:
        elapsed = time.time() - global_start
        log_message("income", f"❌ Erro inesperado: {e}")
        resumo.append({"module": "income", "status": "❌ erro", "elapsed": elapsed, "started_at": None, "rows": None})
    # --- Executa BU ---
    try:
        resumo.append(run_with_timing("api_businessUnits", run_bu))
    except Exception as e:
        elapsed = time.time() - global_start
        log_message("api_businessUnits", f"❌ Erro inesperado: {e}")
        resumo.append({"module": "api_businessUnits", "status": "❌ erro", "elapsed": elapsed, "started_at": None, "rows": None})
    # --- Executa MVW ---
    try:
        resumo.append(run_with_timing("mvw_atualizacao", run_mvw))
    except Exception as e:
        elapsed = time.time() - global_start
        log_message("mvw_atualizacao", f"❌ Erro inesperado: {e}")
        resumo.append({"module": "mvw_atualizacao", "status": "❌ erro", "elapsed": elapsed, "started_at": None, "rows": None})

    # --- Resumo final ---
    elapsed_total = time.time() - global_start
    log_message("sienge_main", "Resumo da execução main:")
    for r in resumo:
        log_message(
            "sienge_main",
            f"{r['module']} - status: {r['status']} - início: {r['started_at']} - tempo: {r['elapsed']:.2f}s - linhas: {r['rows']}")
    log_message("sienge_main", f"Execução global concluída em {elapsed_total:.2f}s")

if __name__ == "__main__":
    main()
