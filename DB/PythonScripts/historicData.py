import sys, string
import codecs
import netrc
import psycopg2

from os import listdir
from os.path  import isfile, join

from sqlCont import SqlCont
from oztools import oztools

__author__="Olmo S. Zavala Romero"


if __name__ == "__main__":

    fromY = 2012
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
        print(currFile)
        dateFormat = oztools.findDateFormat(currFile)
        #print(dateFormat)
        if year < 2012:
            sqlCont.insertIntoDB(currFile, conn, dateFormat, year,oztools)
        else:
            sqlCont.insertIntoDBAfter2011(currFile, conn, dateFormat, year,sqlCont,oztools)
        year = year + 1

    conn.close()
