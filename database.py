import psycopg2

def get_connection():
    return psycopg2.connect(
        host="localhost",
        database="edugenagent",
        user="postgres",
        password="Arghadip",  # <-- replace this
        port="5432"
    )