class oztools:

    def __init__(self):
        """Constructor of the class"""

    def getCSVfiles(self,mypath,fromY, toY):
        years = range(fromY,toY)
        files = []
        for year in years:
            currFile = "%s/contaminantes_%s.csv" % (mypath,year)
            files.append(currFile)

        return files

    def getTables(self):
        return ['cont_pmco','cont_pmdoscinco' ,'cont_nox' ,'cont_codos' ,'cont_co' ,'cont_nodos' ,'cont_no' ,'cont_otres' ,'cont_sodos', 'cont_pmdiez']

    def findTable(self,fileName):
        if "PM2.5" in fileName:
            return "cont_pmdoscinco"

        if "PM10" in fileName:
            return "cont_pmdiez"

        if "NOX" in fileName:
            return "cont_nox"

        if "CO2" in fileName:
            return "cont_codos"

        if "PMCO" in fileName:
            return "cont_pmco"

        if "CO" in fileName:
            return "cont_co"

        if "NO2" in fileName:
            return "cont_nodos"

        if "NO" in fileName:
            return "cont_no"

        if "O3" in fileName:
            return "cont_otres"

        if "SO2" in fileName:
            return "cont_sodos"

    def findDateFormat(self,fileName):
        "Obtains the date format"
        firstData = 11
        f = open(fileName)
        values = f.readlines()[11:]
        for line in values:
            allDate = (line.rstrip().split(',')[0]).split('/')
            #print allDate
            if int(allDate[0]) > 12:
                return "DD/MM/YYY/HH24"
                break
            else:
                if int(allDate[1]) > 12:
                    return "MM/DD/YYY/HH24"
                    break


