import codecs

def addUnitsToDB(fileName, conn):
    "Reads and prints all the lines in a file"

    print("Filling units into DB...")
    #The with statment is used as a try, catch finally
    text = ''
    cur = conn.cursor();
    f = codecs.open(fileName,'r','iso-8859-1')

    # Skiping header lines
    afterFirstLine =  f.readlines()[2:]

    #If you want to iterate manually use file.readline()
    for line in afterFirstLine:
        unidad = line.split(',')

        sql = "INSERT INTO cont_units (id,unit,nombre) VALUES (%s, %s,%s) "

        cur.execute(sql, (unidad[0], unidad[1],unidad[2]))

    conn.commit()
    cur.close()
    print("Done!")

def addUnits(conn, sqlCont, unitsFile):
    """ This function is in charge of filling the units table from a text file"""

    currTable = "cont_units"

    # Delete previous table
    ans = raw_input("You want to delete data inside the "+currTable+" table (Y or N)? ")
    if ans == 'Y':
        print("Droping table "+currTable+" ...")
        sqlCont.clearTable(conn, currTable)
    else:
        print("Not droping table!")

    # Inserting data
    addUnitsToDB(unitsFile,conn)
