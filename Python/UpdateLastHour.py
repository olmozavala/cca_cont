import sys

# sys.path.insert(0, './libs')
# sys.path.insert(0, '/ServerScripts/Air_Quality_DB/libs')

from pandas import Series, DataFrame
import pandas as pd
import numpy as np
import psycopg2
from psycopg2 import errorcodes
from libs.ozdb import Ozdb
from libs.sqlCont import SqlCont
from libs.oztools import ContIOTools
from datetime import datetime

def main():
    sqlCont = SqlCont()  # Initializes our main class SqlCont
    conn = sqlCont.getPostgresConn()  # Gets a connection to the database
    ozTools = ContIOTools() # Initialize 'helper' object

    # Obtains current month and year
    today = datetime.now();
    month = today.month
    year = today.year
    day = today.day
    hour = today.hour

    readLastHours = 10

    # Updating the contaminantes tables
    tables = ozTools.getTables()
    parameters = ozTools.getContaminants()
    print(F"Updating pollutants tables with the last {readLastHours} hours")
    updateTables(sqlCont, conn, ozTools, tables, parameters, month, year, day, hour, readLastHours=readLastHours)

    # Updating the meteorolgical tables
    tables = ozTools.getMeteoTables()
    parameters = ozTools.getMeteoParams()
    updateTables(sqlCont, conn, ozTools, tables, parameters, month, year, day, hour, readLastHours=readLastHours)

def insertToDB( fecha, id_est, value, table, conn):
    """ This function  inserts single values into the specified table """
    dateFormat = "MM/DD/YYY/HH24"
    sql =  "SET TimeZone='UTC'; INSERT INTO %s (fecha, val, id_est) VALUES (to_timestamp('%s','%s'), '%s', '%s')\n" % (table, fecha,  dateFormat, value, id_est)
    cur = conn.cursor();
    try:
        cur.execute(sql);
        conn.commit()
    except psycopg2.IntegrityError as e:
        # print('Failed to insert query, CODE:', e.pgcode, " Detail: ", errorcodes.lookup(e.pgcode[:2]))
        print("Row already existed!")

    except psycopg2.DatabaseError as e:
        cur.close()
        conn.rollback()


def updateTables(sqlCont, conn, ozTools, tables, parameters, month, year, day, hour, readLastHours=10):
    """ This function  obtains the data for the last month and depending on the received
    month, year, day and hour it tries to store the last readLastHours hours into the database.
    """
    # For each table load the info of current month
    for idx,table in enumerate(tables):
        cont = parameters[idx]

        url = "http://www.aire.cdmx.gob.mx/estadisticas-consultas/concentraciones/respuesta.php?qtipo=HORARIOS&parametro=%s&anio=%s&qmes=%s" % (cont,year,month)
        print(F"Reading data from: {url}")

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
        print(F"Yesterday str: {yesterdayStr}   Today str: {todayStr} From hour: {fromHour}")

        # In this case we need to read hours from the previous day
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
        data = data.reset_index(drop=True)
        
        print("Inserting into DB table ", table, " .....")
        for rowId in range(len(data)):
            row = data.iloc[rowId]
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


if __name__ == "__main__":
    main()
