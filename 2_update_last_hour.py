#!/usr/bin/env python3
"""
Script to update pollutant and meteorological data from the last few hours.
This script fetches data from the Mexico City air quality API and inserts it into the database.
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List
import logging
import warnings
import argparse

# Add the db_utils directory to the path
sys.path.insert(0, './db_utils')

from db_utils.oztools import ContIOTools
from db_utils.queries_add import insert_data
from db_utils.sql_con import num_string, clean_data_value
from db_utils.html_reader import read_html

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Suppress BeautifulSoup encoding warnings
warnings.filterwarnings("ignore", message="You provided Unicode markup but also provided a value for from_encoding")


def parse_date_string(date_str: str) -> tuple[int, int, int]:
    """
    Parse date string in format YYYY-MM-DD or DD-MM-YYYY.
    
    Args:
        date_str (str): Date string to parse
        
    Returns:
        tuple[int, int, int]: (year, month, day)
        
    Raises:
        ValueError: If date format is invalid
    """
    try:
        # Try YYYY-MM-DD format first
        if len(date_str.split('-')[0]) == 4:
            year, month, day = map(int, date_str.split('-'))
        else:
            # Assume DD-MM-YYYY format
            day, month, year = map(int, date_str.split('-'))
        
        # Validate date components
        if not (1 <= month <= 12 and 1 <= day <= 31 and year > 1900):
            raise ValueError("Invalid date components")
            
        return year, month, day
    except Exception as e:
        raise ValueError(f"Invalid date format: {date_str}. Expected YYYY-MM-DD or DD-MM-YYYY. Error: {e}")


def validate_hour(hour: int) -> int:
    """
    Validate and return hour value.
    
    Args:
        hour (int): Hour value to validate
        
    Returns:
        int: Validated hour value
        
    Raises:
        ValueError: If hour is not between 0 and 23
    """
    if not (0 <= hour <= 23):
        raise ValueError(f"Hour must be between 0 and 23, got: {hour}")
    return hour


def validate_hours_to_read(hours: int) -> int:
    """
    Validate and return number of hours to read.
    
    Args:
        hours (int): Number of hours to validate
        
    Returns:
        int: Validated number of hours
        
    Raises:
        ValueError: If hours is not positive
    """
    if hours <= 0:
        raise ValueError(f"Number of hours to read must be positive, got: {hours}")
    return hours


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

        data, url = read_html(cont, year, month)

        if data is None:
            logger.error(f"Error reading data from {url}: All encoding attempts failed")
            continue

        stations = data.keys()

        # From which hour we will try to insert data
        from_hour = (hour - read_last_hours) % 24

        # Today and yesterday dates as strings
        yesterday_str = f"{num_string(day-1)}-{num_string(month)}-{year}"
        today_str = f"{num_string(day)}-{num_string(month)}-{year}"
        logger.info(f"Yesterday str: {yesterday_str}   Today str: {today_str} From hour: {from_hour}")

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
        
        logger.info(f"Inserting into DB table {table} .....")
        success_count = 0
        total_count = 0
        
        for row_id in range(len(today_data)):
            row = today_data.iloc[row_id]
            # Use .iloc[] to avoid deprecation warnings
            fecha_split = row.iloc[0].split('-')

            # We need to substract 1 since hours in the database are 0-23   
            hour = row.iloc[1] - 1
            # Convert date format: DD-MM-YYYY to MM/DD/YYYY HH24:MI:SS
            fecha = f"{fecha_split[1]}/{fecha_split[0]}/{fecha_split[2]} {str(hour)}:00:00"
            
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
                    if insert_data(table, fecha, str(stations[col_id]), str(value_native)):
                        success_count += 1
        
        logger.info(f"Done! Inserted {success_count}/{total_count} records into {table}")


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Update pollutant and meteorological data from the last few hours",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Update with current date/time and 3 hours back
  python 2_update_last_hour.py
  
  # Update with specific date, hour, and number of hours
  python 2_update_last_hour.py --date 2024-01-15 --hour 14 --hours 6
  
  # Update with date in DD-MM-YYYY format
  python 2_update_last_hour.py --date 15-01-2024 --hour 14 --hours 6
        """
    )
    
    parser.add_argument('--date', type=str, default=datetime.now().strftime('%Y-%m-%d'), help='Start date in YYYY-MM-DD or DD-MM-YYYY format (default: current date)')
    parser.add_argument('--hour', type=int, default=datetime.now().hour, help='Start hour (0-23) (default: current hour)')
    parser.add_argument('--hours', type=int, default=3, help='Number of hours to read from the past (default: 3)')
    parser.add_argument('--log-level', type=str, default='INFO', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       help='Set the logging level')
    
    return parser.parse_args()


def main() -> None:
    """
    Main function to update pollutant and meteorological data.
    """
    # Parse command line arguments
    args = parse_arguments()
    
    logger.info("Starting data update process...")
    
    # Initialize helper object
    oz_tools = ContIOTools()

    # Get current date and time as defaults
    today = datetime.now()
    current_month = today.month
    current_year = today.year
    current_day = today.day
    current_hour = today.hour

    # Use provided arguments or defaults
    if args.date:
        try:
            year, month, day = parse_date_string(args.date)
        except ValueError as e:
            logger.error(f"Invalid date format: {e}")
            sys.exit(1)
    else:
        year, month, day = current_year, current_month, current_day
    
    if args.hour is not None:
        try:
            hour = validate_hour(args.hour)
        except ValueError as e:
            logger.error(f"Invalid hour: {e}")
            sys.exit(1)
    else:
        hour = current_hour
    
    try:
        read_last_hours = validate_hours_to_read(args.hours)
    except ValueError as e:
        logger.error(f"Invalid hours to read: {e}")
        sys.exit(1)

    logger.info(f"Using date: {year}-{month:02d}-{day:02d}, hour: {hour}, reading {read_last_hours} hours back")

    # Update pollutant tables
    tables = oz_tools.getTables()
    parameters = oz_tools.getContaminants()
    logger.info(f"Updating pollutants tables with the last {read_last_hours} hours")
    update_tables(oz_tools, tables, parameters, month, year, day, hour, read_last_hours=read_last_hours)

    # Update meteorological tables
    tables = oz_tools.getMeteoTables()
    parameters = oz_tools.getMeteoParams()
    logger.info(f"Updating meteorological tables with the last {read_last_hours} hours")
    update_tables(oz_tools, tables, parameters, month, year, day, hour, read_last_hours=read_last_hours)
    
    logger.info("Data update process completed!")


if __name__ == "__main__":
    main()
