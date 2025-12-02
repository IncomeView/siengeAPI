import os, traceback
from datetime import datetime
from zoneinfo import ZoneInfo
from api_financialCategory import get_financialCategories
from db_utils import save_dataframe
from config import POSTGRES_SCHEMA

LOG_FILE = os.path.join(os.path.dirname(__file__), "execution_log.txt")

"""Salva mensagens em um arquivo físico com timestamp e módulo."""
def log_message(module: str, message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] [{module}] {message}"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry + "\n")
    print(entry)  # também mostra no console

def main():
    # --- Módulo api_financialCategories ---
    try:
        df = get_financialCategories()
        if df is not None:
            df["upDate"] = datetime.now(ZoneInfo("America/Sao_Paulo"))
            log_message("api_financialCategories", f"Transformação concluída, linhas expandidas: {len(df)}")
            log_message("api_financialCategories", str(df.head()))
        else:
            log_message("api_financialCategories", "Não foi possível obter ou transformar os dados.")
            return  # encerra se não houver dados
    except Exception as e:
        log_message("api_financialCategories", f"Erro: {e}")
        log_message("api_financialCategories", traceback.format_exc())
        return

    # --- Módulo Banco ---
    try:
        save_dataframe(df, "FinancialCategories", POSTGRES_SCHEMA)
        log_message("DB", "Dados salvos com sucesso no Postgres.")
    except Exception as e:
        log_message("DB", f"Erro ao salvar no banco: {e}")
        log_message("DB", traceback.format_exc())

if __name__ == "__main__":
    main()
