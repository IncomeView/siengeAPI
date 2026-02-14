import traceback
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import text
from db_utils import get_engine

# lista das materialized views que você quer atualizar
MATERIALIZED_VIEWS = [
    '"sienge"."mvw_inicializacaoSaldo"',
    '"sienge"."mvw_Date"',
    '"sienge"."mvw_saldo_billId"',
    '"sienge"."mvw_saldo_idDocument"'
]

def log_message(module: str, message: str):
    timestamp = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{module}] {message}", flush=True)

def refresh_view(conn, view_name: str, module: str):
    start = time.time()
    started_at = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn.execute(text(f'REFRESH MATERIALIZED VIEW {view_name};'))
        result = conn.execute(text(f'SELECT COUNT(*) FROM {view_name};'))
        row_count = result.scalar()
        elapsed = time.time() - start
        log_message(module, f"{view_name} - status: ✅ ok - início: {started_at} - tempo: {elapsed:.2f}s - linhas: {row_count}")
        return {"view": view_name, "status": "✅ ok", "rows": row_count, "elapsed": elapsed}
    except Exception as e:
        elapsed = time.time() - start
        log_message("sienge_refresh_mvw", f"Erro ao atualizar {view_name}: {e}")
        log_message("sienge_refresh_mvw", traceback.format_exc())
        return {"view": view_name, "status": "❌ erro", "rows": None, "elapsed": elapsed}

def refresh_views(module: str = "sienge_refresh_mvw"):
    global_start = time.time()
    started_at = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%Y-%m-%d %H:%M:%S")

    engine = get_engine()
    resumo = []
    with engine.begin() as conn:
        for view in MATERIALIZED_VIEWS:
            resumo.append(refresh_view(conn, view, module))

    # --- Resumo final ---
    elapsed = time.time() - global_start
    log_message(module, "Resumo da execução:")
    log_message(
        module,
        f"Processo completo - status: {'✅ ok' if all(r['status']=='✅ ok' for r in resumo) else '⚠️ parcial'} "
        f"- início: {started_at} - tempo total: {elapsed:.2f}s - views atualizadas: {len(resumo)}")

if __name__ == "__main__":
    refresh_views()
