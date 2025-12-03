from sqlalchemy import text
from db_utils import get_engine

# lista das materialized views que você quer atualizar
MATERIALIZED_VIEWS = [
    "sienge.mvw_mainUnits",
    "sienge.mvw_salesContract",
    "sienge.mvw_Companies"
    "sienge.mvw_inicializacaoSaldo"
    "sienge.mvw_Date"
]

def refresh_views():
    engine = get_engine()
    with engine.begin() as conn:
        for view in MATERIALIZED_VIEWS:
            print(f"Atualizando {view}...")
            conn.execute(text(f'REFRESH MATERIALIZED VIEW CONCURRENTLY {view};'))
    print("Todas as materialized views foram atualizadas com sucesso!")

if __name__ == "__main__":
    refresh_views()