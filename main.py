from postgresqlHelper.postgresqlHelper import postgresqlConnector
import postgresqlHelper.sqlQueries
import os
from fragmentMemoryCalculator.fragmentMemoryCalculator import hexdecode_and_decompress

envdbhost = os.environ.get('envdbhost')
envdbport = os.environ.get('envdbport')
envdbname = os.environ.get('envdbname')
envdbuser = os.environ.get('envdbuser')
envdbpass = os.environ.get('envdbpass')

postgres_conn = postgresqlConnector(dbhost=envdbhost,
                                    dbport=envdbport,
                                    dbname=envdbname,
                                    dbuser=envdbuser,
                                    dbpass=envdbpass)


if __name__ == '__main__':
    # get all fragmented variables from db (hexencoded and compressed)
    sql_query = postgresqlHelper.sqlQueries.query_fragment_variables_for_token('part1')
    results = postgres_conn.run_query(query_str=sql_query)
    # combine bytestrings
    combined_bytes = ''.join([val for varname, val in results])
    length_of_json_in_db = len(combined_bytes)
    raw_json = hexdecode_and_decompress(combined_bytes)
    print()