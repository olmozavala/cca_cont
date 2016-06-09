import psycopg2
import netrc

class SqlCont:


    def __init__(self):
        """Constructor of the class"""

    def getPostgresConn(self):
        secrets = netrc.netrc()
        #print secrets
        #print secrets.hosts
        login, account, passw = secrets.hosts['OWGIS']

        #For Posgresql only
        try:
            conn = psycopg2.connect(database="contingencia", user=login, host='132.248.8.238', password=passw)
        except:
            print "Failed to connect to database"

        return conn

    def delFromYear(self,year,tables,conn):
        text = "Are you sure you want to delete from year: %s (Y or N)? " % (year)
        ans = raw_input(text)
        if ans == 'Y':
            cur = conn.cursor();
            for table in tables:
                print "Deleting table %s from year %s" % (table,year)
                sql = "DELETE FROM %s WHERE date_part('year',fecha) >= %s ;" % (table,year)
                cur.execute(sql)
                conn.commit()
        else:
            print "Not droping tables!"

    def getContaminantes(self,conn):
        cur = conn.cursor();
        cur.execute(""" SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'; """);
        rows = cur.fetchall();

        return rows

