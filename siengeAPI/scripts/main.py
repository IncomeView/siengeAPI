import traceback
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from api_financialCategory import main as run_financial_category
from api_customers import main as run_customers

def log_message(module: str, message: str):
    timestamp = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{module}] {message}")

def run_with_timing(module_name: str, func):
    """Executa uma função, loga checkpoints e tempo de execução."""
    log_message(module_name, "Iniciando execução...")
    start = time.time()
    try:
        # --- checkpoint inicial ---
        log_message(module_name, "Checkpoint: início da rotina.")
        # executa a função principal
        result = func()
        # --- checkpoint final ---
        log_message(module_name, "Checkpoint: rotina concluída.")
        elapsed = time.time() - start
        # se a função retornou um DataFrame, loga quantidade de registros
        try:
            import pandas as pd
            if isinstance(result, pd.DataFrame):
                log_message(module_name, f"Total de registros processados: {len(result)}")
        except Exception:
            pass
        log_message(module_name, f"Execução concluída em {elapsed:.2f} segundos.")
        return {"module": module_name, "status": "ok", "elapsed": elapsed}
    except Exception as e:
        elapsed = time.time() - start
        log_message(module_name, f"Erro após {elapsed:.2f} segundos: {e}")
        log_message(module_name, traceback.format_exc())
        return {"module": module_name, "status": "erro", "elapsed": elapsed}

def main():
    resumo = []
    # --- Executa financialCategory ---
    resumo.append(run_with_timing("financialCategory", run_financial_category))
    # --- Executa customers ---
    resumo.append(run_with_timing("customers", run_customers))

    # --- Resumo final ---
    log_message("sienge_main", "Resumo da execução:")
    for r in resumo:
        log_message("sienge_main", f"{r['module']} - status: {r['status']} - tempo: {r['elapsed']:.2f}s")

if __name__ == "__main__":
    main()
