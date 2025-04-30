import psycopg

CONNECTION = None

def get_database_connection(db_name="", db_user="", db_password="", db_host="", db_port=5432):
    global CONNECTION
    if CONNECTION:
        return CONNECTION
    else:
        try:
            CONNECTION = psycopg.connect(
                dbname=db_name,
                user=db_user,
                password=db_password,
                host=db_host,
                port=db_port,
            )
            CONNECTION.autocommit = True
            return CONNECTION

        except psycopg.OperationalError as e:
            print(f"Encountered error: {e}")
            return None
        
def db_setup(table, schema, conn):
    query = f"""
        CREATE TABLE IF NOT EXISTS {table}({", ".join([f"{k} {v}" for (k,v) in schema.items()])})
    """

    conn.cursor().execute(query)
