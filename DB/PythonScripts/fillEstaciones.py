import sys, string
__author__="Olmo S. Zavala Romero"

#for Posgresql only
import psycopg2

def fillEstaciones(fileName, conn):
    "Reads and prints all the lines in a file"
    #The with statment is used as a try, catch finally
    text = ''
    cur = conn.cursor();
    with open(fileName) as f:
        afterFirstLine =  f.readlines()[2:]

        #If you want to iterate manually use file.readline()
        for line in afterFirstLine:
            estacion = line.split(',')
            print estacion
            sql = "INSERT INTO cont_estaciones VALUES (%s, %s) " 
            cur.execute(sql, (estacion[0], estacion[1]))


    conn.commit()
    cur.close()
    conn.close()

def postgresqlExamle():
    #For Posgresql only
    try: 
        conn = psycopg2.connect("dbname='contingencia' user='argel' host='132.248.8.238' password='contargel'")
    except:
        print "Failed to connect to database"

    return conn


if __name__ == "__main__":
    fileName = "../../RAMA_CSV/CLV_estaciones.csv"
    conn = postgresqlExamle()
    fillEstaciones(fileName, conn)


