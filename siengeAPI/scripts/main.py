import traceback, time, pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
from api_financialCategory import main as run_financial_category
from api_customers import main as run_customers
from mvw_atualizacao import refresh_views as run_mvw
from BU_businessUnits import main as run_bu


def log_message(module: str, message: str):
    timestamp = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{module}] {message}")

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
    resumo.append(run_with_timing("financialCategory", run_financial_category))
    # --- Executa customers ---
    resumo.append(run_with_timing("customers", run_customers))
    # --- Executa BU ---
    resumo.append(run_with_timing("BU_businessUnits", run_bu))
    # --- Executa MVW ---
    resumo.append(run_with_timing("mvw_atualizacao", run_mvw))

    # --- Resumo final ---
    elapsed_total = time.time() - global_start
    log_message("sienge_main", "Resumo da execução:")
    for r in resumo:
        log_message(
            "sienge_main",
            f"{r['module']} - status: {r['status']} - início: {r['started_at']} - tempo: {r['elapsed']:.2f}s - linhas: {r['rows']}")
    log_message("sienge_main", f"Execução global concluída em {elapsed_total:.2f}s")

if __name__ == "__main__":
    main()
