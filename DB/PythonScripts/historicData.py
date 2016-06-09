import sys, string
import codecs
import netrc
import psycopg2

from os import listdir
from os.path  import isfile, join

from sqlCont import SqlCont
from oztools import oztools

__author__="Olmo S. Zavala Romero"

def insertIntoDBAfter2011(fileName, conn, dateFormat, year, sqlCont):
    "Filling data into Database mode AFTER 2011"
    print "Filling data into Database mode AFTER 2011"
    cur = conn.cursor();
    f = open(fileName)

    firstData = 11
    addMe = -1

    values = f.readlines()[firstData:]
    c_table = ''
    sqlQueries = {}


    contaminantes = sqlCont.getContaminantes(conn)
    for contaminante in contaminantes:
        sqlQueries[contaminante[0]] = ''

    print "Processing file..."
    count = 0
    for line in values:
        count = count + 1
        lineValues = line.split(',')
        fechaValues =  lineValues[0].split(' ')
        fecha =  fechaValues[0]+'/'+str((int(fechaValues[1].split(':')[0])+addMe))
        id_est =  lineValues[1]
        table =  oztools.findTable(lineValues[2])
        myval =  lineValues[3]

        if myval != '':
            if sqlQueries[table] == '':
                print "Filling something in table: ",table
                sqlQueries[table] = "SET TimeZone='UTC'; INSERT INTO %s (fecha, val, id_est) VALUES (to_timestamp('%s','%s'), '%s', '%s')\n" % (table, fecha,  dateFormat, myval, id_est)
            else:
                sqlQueries[table] = sqlQueries[table] + " ,(to_timestamp('%s','%s'), '%s', '%s')\n" % (fecha,  dateFormat, myval, id_est)


        if count % 100000 == 0:
            print count
            for mykey in sqlQueries.keys():
                sql = sqlQueries[mykey]
                if sql != '':
                    #print "Inserting in:",mykey
                    cur.execute(sql)
                    conn.commit()
                    sqlQueries[mykey] = ''


    for mykey in sqlQueries.keys():
        sql = sqlQueries[mykey]
        if sql != '':
            #print "Inserting in:",mykey
            cur.execute(sql)
            conn.commit()
            sqlQueries[mykey] = ''

def insertIntoDB(fileName, conn, dateFormat, year):
    "Filling data into Database mode UNTIL 2011"
    print "Filling data into Database mode UNTIL 2011"
    cur = conn.cursor();
    #f = codecs.open(fileName,'r','iso-8859-1')
    f = open(fileName)
    firstData = 11

    addMe = -1

    values = f.readlines()[firstData:]
    sql = ''
    c_table = ''

    for line in values:
        lineValues = line.split(',')
        fechaValues =  lineValues[0].split(' ')
        fecha =  fechaValues[0]+'/'+str((int(fechaValues[1].split(':')[0])+addMe))
        id_est =  lineValues[1]
        table =  oztools.findTable(lineValues[2])
        myval =  lineValues[3]

        if(c_table != table):
            if sql != '':
                print c_table
                #Run query
                #try:
                cur.execute(sql)
                conn.commit()
                #except:
                #raw_input("Press Enter to continue...")

            c_table = table
            sql = ''
            firstLine = True

        if myval != '':
            #print myval
            if firstLine:
                sql =  "SET TimeZone='UTC'; INSERT INTO %s (fecha, val, id_est) VALUES (to_timestamp('%s','%s'), '%s', '%s')\n" % (table, fecha,  dateFormat, myval, id_est)
                firstLine = False
            else:
                sql = sql +  " ,(to_timestamp('%s','%s'), '%s', '%s')\n" % (fecha,  dateFormat, myval, id_est)

            #print sql

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

if __name__ == "__main__":

    fromY = 2015
    toY = 2017

    sqlCont = SqlCont()
    oztools= oztools()
    conn = sqlCont.getPostgresConn()

    ## Read all the files from where to upload data
    files = oztools.getCSVfiles("DataForDB",fromY,toY)

    ##print files
    tables = oztools.getTables()
    sqlCont.delFromYear(fromY,tables,conn)

    ## Iterate over files 
    year = fromY
    for currFile in files:
        # Find the table for current file
        print currFile
        dateFormat = oztools.findDateFormat(currFile)
        if year < 2012:
            insertIntoDB(currFile, conn, dateFormat, year)
        else:
            insertIntoDBAfter2011(currFile, conn, dateFormat, year,sqlCont)
        year = year + 1

    conn.close()
