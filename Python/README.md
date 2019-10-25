Install
-------

Linux (Ubuntu) Libraries:
    
    sudo apt-get install libpq-dev

Python Libraries:

    pip install html5lib, lxml


Configure your credentials by placing a  `.netrc` file
in your  home directory and the proper credentials. 

Don't forget to change the permissions of the netrc to 600.

An example of that file is the following:

    machine MACHINE_NAME
        login USERNAME
        password PSW


Database tables
================

We mainly have 3 types of tables:

* **cont_** Those have all the pollutants, one table for each pollutant. 
* **met_** Those have all the meteorological variables, one table for each variable. 
* **forecast_** Those have the generated forecasts for each pollutant, one table for each pollutant. 
(multiple forecast types in each table.) 

Then we have helper metadata tables:
* **cont_units** It has all the units used for the pollutants. 
* **cont_estaciones** It has the name and location of all the stations. 
* **tipo_pronostico** It has the different types of forecasts being generated. 


Other tables with important data:
* **historical_values** This table has all the 'raw' data (hourly data) from all the pollutants 
needs to be modified because it should be growing very fast. 
* **climatologia** It contains the hourly climatology (by month) for each stations. 


Python Scripts
================

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
