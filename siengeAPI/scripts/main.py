import traceback
from datetime import datetime
from zoneinfo import ZoneInfo
from api_financialCategory import main as run_financial_category
from api_customers import main as run_customers

from db_utils import save_dataframe
from config import POSTGRES_SCHEMA

def log_message(module: str, message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{module}] {message}")

def main():
    # --- Executa financialCategory ---
    try:
        run_financial_category()
        log_message("sienge_main", "Execução de financialCategory concluída.")
    except Exception as e:
        log_message("sienge_main", f"Erro em financialCategory: {e}")
        log_message("sienge_main", traceback.format_exc())

    # --- Executa customers ---
    try:
        run_customers()
        log_message("sienge_main", "Execução de customers concluída.")
    except Exception as e:
        log_message("sienge_main", f"Erro em customers: {e}")
        log_message("sienge_main", traceback.format_exc())

if __name__ == "__main__":
    main()