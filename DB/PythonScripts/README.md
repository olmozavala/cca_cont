Install Anaconda 
---------------------

    conda install -c anaconda html5lib 

FillAndUpdateAirQualityDB.py
----------------------------

This file is the one that stores and updates the DB with air pollution data and 
meteorological data. 

UpdateMonth.py
----------------------------
Updates the data from the specified year and month. 

UpdateLastHour.py
----------------------------
Updates the data from the last 10 hours (from server time). 
It should be executed every hour. 
