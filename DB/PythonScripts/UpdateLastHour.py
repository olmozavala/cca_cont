import sys

sys.path.insert(0, './libs')
sys.path.insert(0, '/ServerScripts/Air_Quality_DB/libs')

from pandas import Series, DataFrame
import pandas as pd
import numpy as np
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
    cur.execute(sql);
    conn.commit()
    try:
        print('nel')
        #cur.execute(sql);
        #conn.commit()
    except psycopg2.DatabaseError as e:
    #except psycopg2.IntegrityError as e:
        if e.pgcode == '25P02':
            print('Failed to insert query, CODE:', e.pgcode, " Detail: ", errorcodes.lookup(e.pgcode[:2]))
        else:
            print('Failed to insert query, CODE:', e.pgcode, " Detail: ", errorcodes.lookup(e.pgcode[:2]))

        cur.close()
        conn.rollback()


def updateTables(sqlCont, conn, ozTools, tables, parameters, month, year, day, hour):
    """ This function  obtains the data for the last month and depending on the received
    month, year, day and hour it tries to store the last readLastHours hours into the database.
    """

    readLastHours = 10# How many previous hours are we going to read

    # For each table load the info of current month
    for idx,table in enumerate(tables):
        cont = parameters[idx]

        url = "http://www.aire.cdmx.gob.mx/estadisticas-consultas/concentraciones/respuesta.php?qtipo=HORARIOS&parametro=%s&anio=%s&qmes=%s" % (cont,year,month)
        print("Reading data from:")
        print(url)

        #allRead = pd.read_html("Test.html", header=1)
        allRead = pd.read_html(url, header=1)

        # The data has two columns 'Fecha' and 'Hora' example: 
        #http://www.aire.df.gob.mx/estadisticas-consultas/concentraciones/respuesta.php?qtipo=HORARIOS&parametro=o3&anio=2017&qmes=12

        data = allRead[0]
        stations = data.keys()

        # From which hour we will try to insert  data
        fromHour = (hour - readLastHours) % 24

        # Today and yesterday dates as strings
        yesterdayStr = numString(day-1)+'-'+numString(month)+'-'+str(year);
        todayStr = numString(day)+'-'+numString(month)+'-'+str(year);
        #print(yesterdayStr)
        #print(todayStr)

        # In this case we need to read hours from the previous day
        #print('hour: ', hour)
        #print('formhour: ', fromHour)
        if hour <= fromHour:
            # Read all from today and only hours above fromHour from yesterday
            dataIndex = np.logical_or(data['Fecha'] == todayStr, \
                        np.logical_and(data['Fecha'] == yesterdayStr, data['Hora'] >= fromHour))
        else:
            # Read  hours above fromHour from today
            dataIndex = np.logical_and(data['Fecha'] == todayStr, data['Hora'] >= fromHour)
            
        # Reduce the size of the original data using the previously calculated index
        TodayData = data[dataIndex]

        # Read the previous readLastHours hours
        data = TodayData
        data = data.reset_index(drop=True);
        
        print("Inserting into DB table ", table, " .....")
        for rowId in range(len(data)):
            row = data.ix[rowId]
            fechaSplit = row[0].split('-')
            # TODO be sure that the hour is the correct hour (from 0 to 23 in the DB)
            fecha = fechaSplit[1]+'/'+fechaSplit[0]+'/'+fechaSplit[2]+' '+str(row[1])+':00:00'
            for colId in range(2,len(row)):
                if row[colId] != 'nr':
                    #print(fecha,  stations[colId], row[colId], table, conn)
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
