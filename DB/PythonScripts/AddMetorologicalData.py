# coding=utf-8
import sys, string
import codecs
import netrc
import psycopg2

from os import listdir
from os.path  import isfile, join

from sqlCont import SqlCont
from oztools import oztools

__author__="Olmo S. Zavala Romero"

# Here is the begining of the file==================
if __name__ == "__main__":

    fromY = 2010
    toY = 2016

    sqlCont = SqlCont()# Inits a class with several SQL scripts
    oztools= oztools() #  Inits a class with several tools
    conn = sqlCont.getPostgresConn() #Gets the connection to the db

    ## Read all the files from where to upload data
    files = oztools.getMeteoFiles("DataForDB/Meteorologia",fromY,toY)

    ##print files
    tables = oztools.getMeteoTables()
    print(tables)
    sqlCont.delFromYear(fromY,tables,conn)

    ## Iterate over files 
    year = fromY
    for currFile in files:
        # Find the table for current file
        print(currFile)
        dateFormat = oztools.findDateFormat(currFile)
        #print(dateFormat)
        if year < 2012:
            sqlCont.insertIntoDB(currFile, conn, dateFormat, year,oztools)
        else:
            sqlCont.insertIntoDBAfter2011(currFile, conn, dateFormat, year,sqlCont,oztools)
        year = year + 1

    conn.close()
