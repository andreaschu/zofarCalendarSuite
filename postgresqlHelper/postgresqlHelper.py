import psycopg2


class postgresqlConnector:
    def __init__(self, dbhost: str, dbport: str, dbname: str, dbuser: str, dbpass: str):
        self.dbhost = dbhost
        self.dbport = dbport
        self.dbname = dbname
        self.dbuser = dbuser
        self.dbpass = dbpass

    def run_query(self, query_str: str) -> list:
        assert 'delete' not in query_str.lower()
        assert 'drop' not in query_str.lower()
        assert 'insert' not in query_str.lower()
        conn = psycopg2.connect(host=self.dbhost,
                                port=self.dbport,
                                database=self.dbname,
                                user=self.dbuser,
                                password=self.dbpass)
        cur = conn.cursor()
        cur.execute(query_str)
        query_results = cur.fetchall()
        cur.close()
        conn.close()
        return query_results

