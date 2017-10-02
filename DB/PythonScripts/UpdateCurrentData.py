import sys

sys.path.insert(0, './libs')
sys.path.insert(0, '/home/olmozavala/Dropbox/TutorialsByMe/Python/PythonExamples/OZLIB/DB')

from pandas import Series, DataFrame
import pandas as pd
import psycopg2
from ozdb import Ozdb
from sqlCont import SqlCont
from oztools import ContIOTools
from datetime import date

def insertToDB( fecha, id_est, value, table, conn):
    """ This function  inserts single values into the specified table """
    dateFormat = "MM/DD/YYY/HH24"
    sql =  "SET TimeZone='UTC'; INSERT INTO %s (fecha, val, id_est) VALUES (to_timestamp('%s','%s'), '%s', '%s')\n" % (table, fecha,  dateFormat, value, id_est)
    cur = conn.cursor();
    try:
        cur.execute(sql);
    except Exception:
        print('Assuming key already existed')
        cur.close()


def updateTables(sqlCont, conn, ozTools, tables, parameters, month, year):

    for idx,table in enumerate(tables):
        cont = parameters[idx]

        url = "http://www.aire.df.gob.mx/estadisticas-consultas/concentraciones/respuesta.php?qtipo=HORARIOS&parametro=%s&anio=%s&qmes=%s" % (cont,year,month)
        print(url)

        #allRead = pd.read_html("Test.html", header=1)
        allRead = pd.read_html(url, header=1)

        data = allRead[0]
        stations = data.keys()

        for rowId in range(len(data)):
            row = data.ix[rowId]
            fechaSplit = row[0].split('-')
            fecha = fechaSplit[1]+'/'+fechaSplit[0]+'/'+fechaSplit[2]+' '+str(row[1]-1)+':00:00'
            for colId in range(2,len(row)):
                if row[colId] != 'nr':
                    insertToDB(fecha,  stations[colId], row[colId], table, conn)


sqlCont = SqlCont() # Initializes our main class SqlCont
conn = sqlCont.getPostgresConn() # Gets a connection to the database
ozTools= ContIOTools()

# Obtains current month and year
today = date.today() 
month = today.month-1
year = today.year

# Updating the contaminantes tables
tables = ozTools.getTables()
parameters = ozTools.getContaminants()
#updateTables(sqlCont, conn, ozTools, tables, parameters,month, year)

# Updating the meteorolgical tables
tables = ozTools.getMeteoTables()
parameters = ozTools.getMeteoParams()
updateTables(sqlCont, conn, ozTools, tables, parameters,month, year)

conn.commit()
