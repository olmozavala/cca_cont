# coding=utf-8
from typing import List


class ContIOTools:
    """This class contains helper methods to manipulate dates, get names for tables and read files by year"""

    def __init__(self) -> None:
        """Constructor of the class"""

    def getCSVfiles(self, mypath: str, fromY: int, toY: int) -> List[str]:
        """
        Get list of CSV file paths for contaminant data.
        
        Args:
            mypath (str): Base path for files
            fromY (int): Start year
            toY (int): End year
            
        Returns:
            List[str]: List of file paths
        """
        years = range(fromY, toY + 1)
        files = []
        for year in years:
            currFile = "%s/contaminantes_%s.csv" % (mypath, year)
            files.append(currFile)

        return files

    def getMeteoFiles(self, mypath: str, fromY: int, toY: int) -> List[str]:
        """
        Get list of CSV file paths for meteorological data.
        
        Args:
            mypath (str): Base path for files
            fromY (int): Start year
            toY (int): End year
            
        Returns:
            List[str]: List of file paths
        """
        years = range(fromY, toY + 1)
        files = []
        for year in years:
            currFile = "%s/meteorología_%s.csv" % (mypath, year)
            files.append(currFile)

        return files

    def getMeteoTables(self) -> List[str]:
        """
        Get list of meteorological table names.
        
        Returns:
            List[str]: List of meteorological table names
        """
        return ['met_tmp', 'met_rh', 'met_wsp', 'met_wdr', 'met_pba']

    def getTables(self) -> List[str]:
        """
        Get list of pollutant table names.
        
        Returns:
            List[str]: List of pollutant table names
        """
        return ['cont_pmco', 'cont_pmdoscinco', 'cont_nox', 'cont_codos', 'cont_co', 
                'cont_nodos', 'cont_no', 'cont_otres', 'cont_sodos', 'cont_pmdiez']

    def getContaminants(self) -> List[str]:
        """
        Get list of pollutant parameter names for API calls.
        
        Returns:
            List[str]: List of pollutant parameter names
        """
        return ['pmco', 'pm2', 'nox', 'co2', 'co', 'no2', 'no', 'o3', 'so2', 'pm10']

    def getMeteoParams(self) -> List[str]:
        """
        Get list of meteorological parameter names for API calls.
        
        Returns:
            List[str]: List of meteorological parameter names
        """
        return ['tmp', 'rh', 'wsp', 'wdr', 'pba']

    def findTable(self, fileName: str) -> str:
        """
        Find the corresponding table name based on file content.
        
        Args:
            fileName (str): Name of the file to analyze
            
        Returns:
            str: Corresponding table name
        """
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

        if "TMP" in fileName:
            return "met_tmp"

        if "RH" in fileName:
            return "met_rh"

        if "WSP" in fileName:
            return "met_wsp"

        if "WDR" in fileName:
            return "met_wdr"

        if "PBA" in fileName:
            return "met_pba"
        
        return ""

    def findDateFormat(self, fileName: str) -> str:
        """
        Obtains the date format from the file.
        
        Args:
            fileName (str): Path to the file to analyze
            
        Returns:
            str: Date format string ("DD/MM/YYY/HH24" or "MM/DD/YYY/HH24")
        """
        firstData = 11
        with open(fileName) as f:
            values = f.readlines()[11:]
            for line in values:
                allDate = (line.rstrip().split(',')[0]).split('/')
                if int(allDate[0]) > 12:
                    return "DD/MM/YYY/HH24"
                else:
                    if int(allDate[1]) > 12:
                        return "MM/DD/YYY/HH24"
        
        return "MM/DD/YYY/HH24"  # Default format


