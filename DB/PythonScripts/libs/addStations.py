import codecs

def fillStationsToDB(fileName, conn):
    "Reads and prints all the lines in a file"
    #The with statment is used as a try, catch finally
    text = ''
    cur = conn.cursor();
    f = codecs.open(fileName,'r','iso-8859-1')

    # Skiping header lines
    afterFirstLine =  f.readlines()[2:]

    #If you want to iterate manually use file.readline()
    for line in afterFirstLine:
        estacion = line.split(',')
        if(estacion[5] == ''):
            lastYear = 5000
        else:
            lastYear = int(estacion[5].split(' ')[3])
            #print lastYear

        if(estacion[4] == ''):
            estacion[4] = 2250


        point = "POINT(%s %s)"%(estacion[2],estacion[3])
        sql = "INSERT INTO cont_estaciones (id,nombre,geom,lastyear,altitude) VALUES (%s, %s,ST_GeomFromText(%s,'4326'),%s,%s) "

        print estacion[1]
        cur.execute(sql, (estacion[0], estacion[1],point,lastYear,estacion[4]))

    conn.commit()
    cur.close()

def addStations(conn, sqlCont, stationsFile):
    currTable = "cont_estaciones"
    # Delete previous table
    ans = raw_input("You want to delete data inside the "+currTable+" table (Y or N)? ")
    if ans == 'Y':
        print("Droping table "+currTable+" ...")
        sqlCont.clearTable(conn, currTable)
    else:
        print "Not droping table!"

    # Inserting data
    fillStationsToDB(myStationsFile,conn)
