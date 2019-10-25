__author__="Olmo S. Zavala Romero"

import sys
# sys.path.insert(0, '/home/olmozavala/Dropbox/TutorialsByMe/Python/PythonExamples/OZLIB/DB')
# sys.path.insert(0, './libs')

import psycopg2
from libs.ozdb import Ozdb
from libs.sqlCont import SqlCont
from libs.oztools import ContIOTools

import libs.addUnits as addUnits
import libs.addStations as addStations

def fillData(conn, ozTools, sqlCont, fromY, toY, files, tables):
    """ This function is used to add historic data from yearly files"""
    sqlCont.delFromYear(fromY,tables,conn)

    ## Iterate over files 
    year = fromY
    for currFile in files:
        # Find the table for current file
        print("\n Adding data from this file: " + currFile)
        dateFormat = ozTools.findDateFormat(currFile)
        #print(dateFormat)
        if year < 2012:
            sqlCont.insertIntoDB(currFile, conn, dateFormat, year,ozTools)
        else:
            sqlCont.insertIntoDBAfter2011(currFile, conn, dateFormat, year,sqlCont,ozTools)
        year = year + 1

if __name__ == "__main__":

    sqlCont = SqlCont()  # Initializes our main class SqlCont
    conn = sqlCont.getPostgresConn()  # Gets a connection to the database
    ozTools= ContIOTools()

    # This section is for adding Units into the database
    ans = input("Do you want to add/update the Units table (Y or N)? ")
    if ans.lower() == 'y':
        unitsFile = "DataForDB/cat_unidades.csv"
        addUnits.addUnits(conn, sqlCont, unitsFile)

    # This section is for adding Stations into the database
    ans = input("Do you want to add/update the stations table (Y or N)? ")
    if ans.lower() == 'y':
        myStationsFile = "DataForDB/cat_estacion.csv"
        addStations.addStations(conn, sqlCont, myStationsFile)

    # This section is for adding historic contaminants data into the database
    ans = input("Do you want to add/update meteorolgy data  files (Y or N)? ")
    if ans.lower() == 'y':
        fromY = int(input("From which year? (integer)"))
        toY= int(input("To which year? (integer)"))
        folder = "DataForDB"
        tables = ozTools.getMeteoTables()
        files = ozTools.getMeteoFiles("DataForDB/Meteorologia",fromY,toY)
        fillData(conn, ozTools, sqlCont, fromY, toY, files, tables)

    # This section is for adding data into the database
    ans = input("Do you want to add/update historic contaminants data  files (Y or N)? ")
    if ans.lower() == 'y':
        fromY = int(input("From which year? (integer)"))
        toY= int(input("To which year? (integer)"))
        folder = "DataForDB"
        ## Read all the files from where to upload data
        files = ozTools.getCSVfiles(folder,fromY,toY)
        tables = ozTools.getTables()
        fillData(conn, ozTools, sqlCont, fromY, toY, files, tables)


    conn.close()
