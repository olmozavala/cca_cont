import sys, string
import codecs
from os import listdir
from os.path  import isfile, join

__author__="Olmo S. Zavala Romero"

#for Posgresql only
import psycopg2

def findDateFormat(fileName):
    "Obtains the date format"
    firstData = 11
    f = open(fileName)
    values = f.readlines()[11:]
    for line in values:
        allDate = (line.rstrip().split(',')[0]).split('/')
        #print allDate
        if int(allDate[0]) > 12:
            return "DD/MM/YYY/HH24"
            break
        else:
            if int(allDate[1]) > 12:
                return "MM/DD/YYY/HH24"
                break


def insertIntoDB(fileName, conn, dateFormat):
    "Filling data into Database"
    #The with statment is used as a try, catch finally
    cur = conn.cursor();
    #f = codecs.open(fileName,'r','iso-8859-1')
    f = open(fileName)
    firstData = 11

    values = f.readlines()[firstData:]
    sql = ''
    c_table = ''

    sql =  "SET TimeZone='UTC';\n" 

    cur.execute(sql)
    conn.commit()

    for line in values:
        lineValues = line.split(',')
        fechaValues =  lineValues[0].split(' ')
        fecha =  fechaValues[0]+'/'+str((int(fechaValues[1].split(':')[0])-1))
        id_est =  lineValues[1]
        table =  findTable(lineValues[2])
        myval =  lineValues[3]

        # Test if there are values in the next month

        sql = ''

        if myval != '':
            sql =  "INSERT INTO %s (fecha, val, id_est) VALUES (to_timestamp('%s','%s'), '%s', '%s')\n" \
                        % (table, fecha,  dateFormat, myval, id_est)
            try:
                cur.execute(sql)
                conn.commit()
            except:
                print "Repeated: ",sql

def delFromYear(year,tables,conn):
    cur = conn.cursor();
    print "Deleting table %s from year %s" % (table,year)
    for table in tables:
        sql = "DELETE FROM %s WHERE date_part('year',fecha) >= %s ;" % (table,year)
        cur.execute(sql)
        conn.commit()


def dropTable(table,conn,cur):
    print "Deleting table %s" % (table)
    sql = "DELETE FROM %s WHERE true;" % (table)
    cur.execute(sql)
    conn.commit()

def cleanTable(table,conn,cur):
    print "Cleaning wrong values for table %s" % (table)
    sql = "DELETE FROM %s WHERE val = '-99';" % (table)
    cur.execute(sql)
    conn.commit()

def restartSeq(table,conn,cur):
    seq = "cont_seq_"+(table.replace("cont_",""))
    print "Setting sequence = 1 for seq %s" % (seq)
    sql = "ALTER SEQUENCE %s RESTART WITH 1" % (seq)
    print sql
    cur.execute(sql)
    conn.commit()

def restartAllSeq(conn,tables):
    cur = conn.cursor()
    for table in tables:
        restartSeq(table,conn,cur)

    cur.close();

def dropAll(conn,tables):
    ans = raw_input("Are SURE YOU WANT TO DELETE ALL DATA (Y or N)? ")
    if ans == 'Y':
        cur = conn.cursor()
        for table in tables:
            dropTable(table,conn,cur)

        cur.close();
        restartAllSeq(conn,tables)
    else:
        print "Not droping tables!"

def cleanAll(conn,tables):
    cur = conn.cursor()
    for table in tables:
        cleanTable(table,conn,cur)

    cur.close();

def getPostgresConn():
    #For Posgresql only
    try:
        conn = psycopg2.connect("dbname='contingencia' user='argel' host='132.248.8.238' password='contargel'")
    except:
        print "Failed to connect to database"

    return conn

def findTable(fileName):
    if "PM2.5" in fileName:
        return "cont_pmdoscinco"

    if "PM10" in fileName:
        return "cont_pmdiez"

    if "NOX" in fileName:
        return "cont_nox"

    if "CO2" in fileName:
        return "cont_codos"

    if "CO" in fileName:
        return "cont_co"

    if "NO2" in fileName:
        return "cont_nodos"

    if "NO" in fileName:
        return "cont_no"

    if "O3" in fileName:
        return "cont_otres"

    if "SO2" in fileName:
        return "cont_sodos"

    if "PMCO" in fileName:
        return "cont_pmco"

def getFiles(mypath,fromY, toY):
    years = range(fromY,toY)
    files = []
    for year in years:
        currFile = "%s/contaminantes_%s.csv" % (mypath,year)
        files.append(currFile)

    return files

if __name__ == "__main__":
    fromY = 2016 
    toY = 2016

    # Read all the files from where to upload data
    files = getFiles("DataForDB",fromY,toY)

    #print files
    conn = getPostgresConn()
    delFromYear(fromY,conn)

    tables = [ 'cont_pmdoscinco' ,'cont_nox' ,'cont_codos' ,'cont_co' ,'cont_nodos' ,'cont_no' ,'cont_otres' ,'cont_sodos', 'cont_pmdiez']

# Iterate over files 
    for currFile in files:
        # Find the table for current file
        print currFile
        dateFormat = findDateFormat(currFile)
        insertIntoDB(currFile, conn, dateFormat)

    conn.close()
