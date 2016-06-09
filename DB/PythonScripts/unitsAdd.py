import sys, string
import base64
__author__="Olmo S. Zavala Romero"

sys.path.insert(0, '/home/olmozavala/Dropbox/TutorialsByMe/Python/PythonExamples/OZLIB/DB')

#for Posgresql only
import psycopg2
import codecs
from ozdb import Ozdb

def fillUnidades(fileName, conn):
    "Reads and prints all the lines in a file"
    #The with statment is used as a try, catch finally
    text = ''
    cur = conn.cursor();
    f = codecs.open(fileName,'r','iso-8859-1')

    # Skiping header lines
    afterFirstLine =  f.readlines()[2:]

    #If you want to iterate manually use file.readline()
    for line in afterFirstLine:
        unidad = line.split(',')

        sql = "INSERT INTO cont_units (id,unit,nombre) VALUES (%s, %s,%s) "

        cur.execute(sql, (unidad[0], unidad[1],unidad[2]))

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

    myTable = "cont_units"
    myStationsFile = "DataForDB/cat_unidades.csv"
    # Delete previous table
    ans = raw_input("Are SURE YOU WANT TO DELETE ALL DATA (Y or N)? ")
    if ans == 'Y':
        dbman.dropTable(myTable,conn)
    else:
        print "Not droping table!"

    # Inserting data
    fillUnidades(myStationsFile,conn)
