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

def save_dataframe_insert(df, table_name, schema, pk_column="id"):
    """
    UPSERT seguro para APIs.
    update, insert e delete registros conforme a API.
    Requer que Dataframe tenha uma coluna 'id' ou definir o nome da coluna primária.
    """
    engine = get_engine()
    inspector = inspect(engine)
    if pk_column not in df.columns:
        raise ValueError(f"A coluna '{pk_column}' não existe no DataFrame.")

    cols = list(df.columns)
    col_names = ", ".join(f'"{c}"' for c in cols)
    excluded_updates = ", ".join([f'"{c}" = EXCLUDED."{c}"' for c in cols if c != pk_column])

    # cria tabela se não existir
    with engine.begin() as conn:
        if not inspector.has_table(table_name, schema=schema):
            df.head(0).to_sql(table_name, conn, schema=schema, if_exists="replace", index=False)
            conn.execute(text(f'ALTER TABLE "{schema}"."{table_name}" ADD PRIMARY KEY ("{pk_column}");'))

    # UPSERT (INSERT + UPDATE)
    with engine.begin() as conn:
        insert_sql = f"""
            INSERT INTO "{schema}"."{table_name}" ({col_names})
            VALUES ({", ".join([f":{c}" for c in cols])})
            ON CONFLICT ("{pk_column}") DO UPDATE SET
            {excluded_updates};
        """
        conn.execute(text(insert_sql), df.to_dict(orient="records"))

    # DELETE registros que não existem mais na API
    ids_tuple = tuple(df[pk_column].tolist()) or (None,)
    with engine.begin() as conn:
        delete_sql = f"""
            DELETE FROM "{schema}"."{table_name}"
            WHERE "{pk_column}" NOT IN :ids;
        """
        conn.execute(text(delete_sql), {"ids": ids_tuple})
