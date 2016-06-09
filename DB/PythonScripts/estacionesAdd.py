import sys, string
__author__="Olmo S. Zavala Romero"

sys.path.insert(0, '/home/olmozavala/Dropbox/TutorialsByMe/Python/PythonExamples/OZLIB/DB')

#for Posgresql only
import psycopg2
import codecs
from ozdb import Ozdb

def fillEstaciones(fileName, conn):
    "Reads and prints all the lines in a file"
    #The with statment is used as a try, catch finally
    text = ''
    cur = conn.cursor();
    f = codecs.open(fileName,'r','iso-8859-1')

    # Skiping header lines
    afterFirstLine =  f.readlines()[2:]

    #If you want to iterate manually use file.readline()
    for line in afterFirstLine:
        estacion = line.split(',')
        if(estacion[5] == ''):
            lastYear = 5000
        else:
            lastYear = int(estacion[5].split(' ')[3])
            #print lastYear

        if(estacion[4] == ''):
            estacion[4] = 2250


        point = "POINT(%s %s)"%(estacion[2],estacion[3])
        sql = "INSERT INTO cont_estaciones (id,nombre,geom,lastyear,altitude) VALUES (%s, %s,ST_GeomFromText(%s,'4326'),%s,%s) "

        print estacion[1]
        cur.execute(sql, (estacion[0], estacion[1],point,lastYear,estacion[4]))


    conn.commit()
    cur.close()
    conn.close()

def getConn():
    #For Posgresql only
    try:
        conn = psycopg2.connect("dbname='contingencia' user='argel' host='132.248.8.238' password='contargel'")
    except:
        print "Failed to connect to database"

    return conn


if __name__ == "__main__":
    conn = getConn()
    dbman = Ozdb()

    myTable = "cont_estaciones"
    myStationsFile = "DataForDB/cat_estacion.csv"
    # Delete previous table
    ans = raw_input("Are SURE YOU WANT TO DELETE ALL DATA (Y or N)? ")
    if ans == 'Y':
        dbman.dropTable(myTable,conn)
    else:
        print "Not droping table!"

    # Inserting data
    fillEstaciones(myStationsFile,conn)
