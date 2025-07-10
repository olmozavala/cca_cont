#!/usr/bin/env python3
"""
Script to update pollutant and meteorological data from the last few hours.
This script fetches data from the Mexico City air quality API and inserts it into the database.
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Tuple, Optional

# Add the db_utils directory to the path
sys.path.insert(0, './db_utils')

from db_utils.oztools import ContIOTools
from db_utils.queries_add import insert_pollutant_data, insert_meteorological_data


def num_string(num: int) -> str:
    """
    Convert a number to a zero-padded string.
    
    Args:
        num (int): Number to convert
        
    Returns:
        str: Zero-padded string representation
    """
    if num < 10:
        return "0" + str(num)
    else:
        return str(num)


def clean_data_value(value: object) -> str:
    """
    Clean data values by removing special characters and converting to string.
    
    Args:
        value (object): Raw value from the data
        
    Returns:
        str: Cleaned string value
    """
    if pd.isna(value) or value == 'nr':
        return 'nr'
    
    # Convert to string and clean special characters
    value_str = str(value)
    
    # Remove common problematic characters that might appear in PM data
    # Replace μ (micro) with 'u' or remove it
    value_str = value_str.replace('μ', 'u').replace('µ', 'u')
    
    # Remove any other non-numeric characters except decimal points and minus signs
    import re
    # Keep only numbers, decimal points, minus signs, and 'nr'
    if value_str.lower() == 'nr':
        return 'nr'
    
    # Try to extract numeric value
    numeric_match = re.search(r'-?\d*\.?\d*', value_str)
    if numeric_match:
        return numeric_match.group()
    
    return value_str


def insert_to_db(fecha: str, id_est: str, value: str, table: str) -> bool:
    """
    Insert a single measurement into the database.
    
    Args:
        fecha (str): Date string in format 'MM/DD/YYYY HH:MM:SS'
        id_est (str): Station ID
        value (str): Measurement value
        table (str): Table name
        
    Returns:
        bool: True if insertion successful, False otherwise
    """
    if table.startswith('met_'):
        return insert_meteorological_data(table, fecha, id_est, value)
    else:
        return insert_pollutant_data(table, fecha, id_est, value)


def update_tables(oz_tools: ContIOTools, tables: List[str], parameters: List[str], 
                  month: int, year: int, day: int, hour: int, read_last_hours: int = 10) -> None:
    """
    Update tables with data from the last few hours.
    
    Args:
        oz_tools (ContIOTools): Helper object for table and parameter mappings
        tables (List[str]): List of table names to update
        parameters (List[str]): List of parameter names for API calls
        month (int): Current month
        year (int): Current year
        day (int): Current day
        hour (int): Current hour
        read_last_hours (int): Number of hours to read from the past
    """
    # For each table load the info of current month
    for idx, table in enumerate(tables):
        cont = parameters[idx]

        url = f"http://www.aire.cdmx.gob.mx/estadisticas-consultas/concentraciones/respuesta.php?qtipo=HORARIOS&parametro={cont}&anio={year}&qmes={month}"
        print(f"Reading data from: {url}")

        # Try multiple encodings to handle character encoding issues
        encodings_to_try = ['latin-1', 'cp1252', 'iso-8859-1', 'utf-8', None]
        data = None
        
        for encoding in encodings_to_try:
            try:
                if encoding:
                    all_read = pd.read_html(url, header=1, encoding=encoding)
                else:
                    all_read = pd.read_html(url, header=1)
                data = all_read[0]
                print(f"✅ Successfully read data with encoding: {encoding or 'default'}")
                break
            except Exception as e:
                print(f"⚠️  Failed with encoding {encoding or 'default'}: {str(e)[:100]}...")
                continue
        
        if data is None:
            print(f"❌ Error reading data from {url}: All encoding attempts failed")
            continue

        stations = data.keys()

        # From which hour we will try to insert data
        from_hour = (hour - read_last_hours) % 24

        # Today and yesterday dates as strings
        yesterday_str = f"{num_string(day-1)}-{num_string(month)}-{year}"
        today_str = f"{num_string(day)}-{num_string(month)}-{year}"
        print(f"Yesterday str: {yesterday_str}   Today str: {today_str} From hour: {from_hour}")

        # In this case we need to read hours from the previous day
        if hour <= from_hour:
            # Read all from today and only hours above from_hour from yesterday
            data_index = np.logical_or(data['Fecha'] == today_str,
                                      np.logical_and(data['Fecha'] == yesterday_str, data['Hora'] >= from_hour))
        else:
            # Read hours above from_hour from today
            data_index = np.logical_and(data['Fecha'] == today_str, data['Hora'] >= from_hour)
            
        # Reduce the size of the original data using the previously calculated index
        today_data = data[data_index]
        today_data = today_data.reset_index(drop=True)
        
        print(f"Inserting into DB table {table} .....")
        success_count = 0
        total_count = 0
        
        for row_id in range(len(today_data)):
            row = today_data.iloc[row_id]
            # Use .iloc[] to avoid deprecation warnings
            fecha_split = row.iloc[0].split('-')
            # Convert date format: DD-MM-YYYY to MM/DD/YYYY HH:MM:SS
            fecha = f"{fecha_split[1]}/{fecha_split[0]}/{fecha_split[2]} {str(row.iloc[1])}:00:00"
            
            for col_id in range(2, len(row)):
                value = row.iloc[col_id]
                value_clean = clean_data_value(value)
                if value_clean != 'nr':
                    total_count += 1
                    # Convert numpy types to native Python types for meteorology tables
                    if isinstance(value, (np.integer, np.floating)):
                        value_native = value.item()
                    else:
                        value_native = value_clean
                    if insert_to_db(fecha, str(stations[col_id]), str(value_native), table):
                        success_count += 1
        
        print(f"Done! Inserted {success_count}/{total_count} records into {table}")


def main() -> None:
    """
    Main function to update pollutant and meteorological data.
    """
    print("🔄 Starting data update process...")
    
    # Initialize helper object
    oz_tools = ContIOTools()

    # Get current date and time
    today = datetime.now()
    month = today.month
    year = today.year
    day = today.day
    hour = today.hour

    read_last_hours = 10

    # Update pollutant tables
    tables = oz_tools.getTables()
    parameters = oz_tools.getContaminants()
    print(f"📊 Updating pollutants tables with the last {read_last_hours} hours")
    update_tables(oz_tools, tables, parameters, month, year, day, hour, read_last_hours=read_last_hours)

    # Update meteorological tables
    tables = oz_tools.getMeteoTables()
    parameters = oz_tools.getMeteoParams()
    print(f"🌤️  Updating meteorological tables with the last {read_last_hours} hours")
    update_tables(oz_tools, tables, parameters, month, year, day, hour, read_last_hours=read_last_hours)
    
    print("✅ Data update process completed!")


if __name__ == "__main__":
    main()
