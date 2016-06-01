import sys, string
from os import listdir
from os.path  import isfile, join

__author__="Olmo S. Zavala Romero"

#for Posgresql only
import psycopg2

def fillData(mypath, currFile, table, conn):
    "Filling data into Database"
    fileName = mypath+"/"+currFile
    #The with statment is used as a try, catch finally
    cur = conn.cursor();
    with open(fileName) as f:
        headers = f.readline()
        estaciones = headers.rstrip().split(',')[2:]
        print estaciones

        sqls = ["" for x in range(len(estaciones))]
        lineNum = 1
        for line in f:
            values = line.rstrip().split(',')
            fecha = values[0]+'/'+str((int(values[1])-1))
            #print fecha

            idxVal = 0
            for estacion in estaciones:
                if lineNum == 1:
                    sqls[idxVal] = "INSERT INTO %s (fecha, val, id_est) VALUES  (to_timestamp('%s','MM/DD/YYY/HH24'), '%s', '%s')\n" % (table, fecha, values[2+idxVal], estacion)
                    #print sqls[estacion]
                else:
                    sqls[idxVal] = sqls[idxVal]  + ",(to_timestamp('%s','MM/DD/YYY/HH24'), '%s', '%s')\n" % (fecha, values[2+idxVal], estacion)
                    #print sqls[estacion]

                idxVal = idxVal + 1 

            lineNum = lineNum + 1

#    print sqls[0]
#    raw_input("Waiting")

    for sql in sqls:
        #print sql
        cur.execute(sql)

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
        conn = psycopg2.connect("dbname='contingencia' user='postgres' host='132.248.8.238' password='o1q4ellv'")
    except:
        print "Failed to connect to database"

    return conn

def findTable(fileName):
    if "PM25" in fileName:
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

def readFiles():
    fileName = "csvFilesMissing.txt"
    files = [] 
    with open(fileName) as f:
        count = 1;
        for line in f: 
            files.append(line.rstrip()) 
            count = count + 1 

    return files 

if __name__ == "__main__":

    # List files
    mypath = '../../RAMA_CSV'
    # Read all the files from where to upload data
    files = readFiles()
    conn = getPostgresConn()

    tables = [ 'cont_pmdoscinco' ,'cont_nox' ,'cont_codos' ,'cont_co' ,'cont_nodos' ,'cont_no' ,'cont_otres' ,'cont_sodos', 'cont_pmdiez']
    
    #dropAll(conn,tables);

# Iterate over files 
    for currFile in files:
        # Find the table for current file
        table = findTable(currFile)

        print currFile, "--", table

        if table != None:
            # Fill data into table for current file
            fillData(mypath, currFile, table, conn)
            conn.commit()

    #cleanAll(conn,tables)
    conn.close()
