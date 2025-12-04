import traceback
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import text
from db_utils import get_engine

# lista das materialized views que você quer atualizar
MATERIALIZED_VIEWS = [
    '"sienge"."mvw_mainUnits"',
    '"sienge"."mvw_salesContract"',
    '"sienge"."mvw_Companies"',
    '"sienge"."mvw_inicializacaoSaldo"',
    '"sienge"."mvw_Date"',
    '"public"."mvw_contasReceber"'
]

def log_message(module: str, message: str):
    timestamp = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{module}] {message}")

def refresh_view(conn, view_name: str):
    try:
        conn.execute(text(f'REFRESH MATERIALIZED VIEW {view_name};'))
        result = conn.execute(text(f'SELECT COUNT(*) FROM {view_name};'))
        row_count = result.scalar()
        return {"view": view_name, "status": "✅ ok", "rows": row_count}
    except Exception as e:
        log_message("sienge_refresh_mvw", f"Erro ao atualizar {view_name}: {e}")
        log_message("sienge_refresh_mvw", traceback.format_exc())
        return {"view": view_name, "status": "❌ erro", "rows": None}

def refresh_views():
    global_start = time.time()
    started_at = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%Y-%m-%d %H:%M:%S")

    engine = get_engine()
    resumo = []
    with engine.begin() as conn:
        for view in MATERIALIZED_VIEWS:
            resumo.append(refresh_view(conn, view))

    # --- Resumo final ---
    elapsed = time.time() - global_start
    log_message("sienge_refresh_mvw", "Resumo da execução:")
    for r in resumo:
        log_message(
            "sienge_refresh_mvw",
            f"{r['view']} - status: {r['status']} - início: {started_at} - tempo total: {elapsed:.2f}s - linhas: {r['rows']}")

if __name__ == "__main__":
    refresh_views()
