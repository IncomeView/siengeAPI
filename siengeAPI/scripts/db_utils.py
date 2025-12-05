from sqlalchemy import create_engine, text, inspect
from config import POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB

def get_engine():
    return create_engine(
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )

def save_dataframe(df, table_name, schema):
    engine = get_engine()
    inspector = inspect(engine)

    with engine.begin() as conn:
        if not inspector.has_table(table_name, schema=schema):
            df.head(0).to_sql(table_name, conn, schema=schema, if_exists="replace", index=False)
            df.to_sql(table_name, conn, schema=schema, if_exists="append", index=False)
        else:
            conn.execute(text(f'TRUNCATE TABLE "{schema}"."{table_name}" RESTART IDENTITY CASCADE'))
            df.to_sql(table_name, conn, schema=schema, if_exists="append", index=False)
#    print(f"Dados importados com sucesso na tabela {schema}.{table_name}!")

