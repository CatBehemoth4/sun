import psycopg2

def baseconnect(usr, passwd):
    try:
        connection = psycopg2.connect(dbname="SUN", user=usr, password=passwd, host="188.120.240.167", port=5432)
    except:
        return 0, 0, 'ERROR'
    cursor = connection.cursor()
    return cursor, connection, 'OK'