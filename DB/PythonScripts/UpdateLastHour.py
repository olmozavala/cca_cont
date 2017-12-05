import sys

sys.path.insert(0, './libs')

from pandas import Series, DataFrame
import pandas as pd
import psycopg2
from psycopg2 import errorcodes
from ozdb import Ozdb
from sqlCont import SqlCont
from oztools import ContIOTools
from datetime import datetime

def insertToDB( fecha, id_est, value, table, conn):
    """ This function  inserts single values into the specified table """
    dateFormat = "MM/DD/YYY/HH24"
    sql =  "SET TimeZone='UTC'; INSERT INTO %s (fecha, val, id_est) VALUES (to_timestamp('%s','%s'), '%s', '%s')\n" % (table, fecha,  dateFormat, value, id_est)
    cur = conn.cursor();
    try:
        cur.execute(sql);
        conn.commit()
    except psycopg2.DatabaseError as e:
    #except psycopg2.IntegrityError as e:
        if e.pgcode == '25P02':
            print('Failed to insert query, CODE:', e.pgcode, " Detail: ", errorcodes.lookup(e.pgcode[:2]))
        else:
            print('Failed to insert query, CODE:', e.pgcode, " Detail: ", errorcodes.lookup(e.pgcode[:2]))

        cur.close()
        conn.rollback()


def updateTables(sqlCont, conn, ozTools, tables, parameters, month, year, day, hour):

    for idx,table in enumerate(tables):
        cont = parameters[idx]

        url = "http://www.aire.df.gob.mx/estadisticas-consultas/concentraciones/respuesta.php?qtipo=HORARIOS&parametro=%s&anio=%s&qmes=%s" % (cont,year,month)
        print("Reading data from:")
        print(url)


        #allRead = pd.read_html("Test.html", header=1)
        allRead = pd.read_html(url, header=1)

        data = allRead[0]
        stations = data.keys()
        newData= data[data['Fecha'] == numString(day)+'-'+numString(month)+'-'+str(year)];
        data = newData[newData['Hora']== hour];
        data = data.reset_index(drop=True);
        
        print("Inserting into DB.....")
        for rowId in range(len(data)):
            row = data.ix[rowId]
            fechaSplit = row[0].split('-')
            fecha = fechaSplit[1]+'/'+fechaSplit[0]+'/'+fechaSplit[2]+' '+str(row[1])+':00:00'
            for colId in range(2,len(row)):
                if row[colId] != 'nr':
                    insertToDB(fecha,  stations[colId], row[colId], table, conn)
        print("Done!")


def numString(num):
    if num < 10:
        return "0"+str(num)
    else:
        return str(num);

sqlCont = SqlCont() # Initializes our main class SqlCont
conn = sqlCont.getPostgresConn() # Gets a connection to the database
ozTools= ContIOTools()

# Obtains current month and year
today = datetime.now();
month = today.month
year = today.year
day = today.day
hour = today.hour

# Updating the contaminantes tables
tables = ozTools.getTables()
parameters = ozTools.getContaminants()
updateTables(sqlCont, conn, ozTools, tables, parameters, month, year, day, hour)

# Updating the meteorolgical tables
tables = ozTools.getMeteoTables()
parameters = ozTools.getMeteoParams()
updateTables(sqlCont, conn, ozTools, tables, parameters,month, year, day, hour)
