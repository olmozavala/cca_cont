#!/usr/bin/env python3
"""
Script to update pollutant and meteorological data from the last few hours.
This script fetches data from the Mexico City air quality API and inserts it into the database.
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List
import logging
import warnings
import argparse
from db_utils.proj_utils import parse_date_string, validate_hour, validate_hours_to_read

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

def update_tables(oz_tools: ContIOTools, tables: List[str], parameters: List[str], 
                  month: int, year: int, day: int, hour: int, read_last_hours: int = 10) -> None:
    """
    Update tables with data from the last few hours, handling multi-month date ranges.
    
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
    # Define the first and last date (including hours) that will be inserted into the DB
    end_datetime = datetime(year, month, day, hour)
    start_datetime = end_datetime - timedelta(hours=read_last_hours)
    
    logger.info(f"Date range to process: {start_datetime} to {end_datetime}")
    
    # Check if we are covering more than one month or year
    months_to_process = []
    current_date = start_datetime
    
    while current_date <= end_datetime:
        month_key = (current_date.year, current_date.month)
        if month_key not in months_to_process:
            months_to_process.append(month_key)
        current_date += timedelta(hours=1)
    
    # Determine if we're crossing year boundaries
    years_in_range = set(year for year, month in months_to_process)
    if len(years_in_range) > 1:
        logger.info(f"Crossing year boundary: processing {len(years_in_range)} year(s): {sorted(years_in_range)}")
    
    # Determine if we're crossing month boundaries
    if len(months_to_process) > 1:
        logger.info(f"Crossing month boundary: processing {len(months_to_process)} month(s): {months_to_process}")
    else:
        logger.info(f"Processing single month: {months_to_process[0]}")
    
    # For each table and parameter
    for idx, table in enumerate(tables):
        cont = parameters[idx]
        logger.info(f"Processing table: {table} with parameter: {cont}")
        
        total_success_count = 0
        total_total_count = 0
        total_duplicate_count = 0
        
        # Process each month separately
        for year_to_process, month_to_process in months_to_process:
            logger.info(f"Reading data for {month_to_process}/{year_to_process}")
            
            # Read HTML data for this month
            data, url = read_html(cont, year_to_process, month_to_process)
            
            if data is None:
                logger.error(f"Error reading data from {url}: All encoding attempts failed")
                continue
            
            stations = data.keys()
            
            # Filter data for the specific date range within this month
            filtered_data = filter_data_for_date_range(data, start_datetime, end_datetime)
            
            if filtered_data.empty:
                logger.info(f"No data found for {table} in {month_to_process}/{year_to_process}")
                continue
            
            logger.info(f"Found {len(filtered_data)} records for {table} in year {year_to_process} and month {month_to_process} for the date range {start_datetime} to {end_datetime}")
            
            # Insert the filtered data
            success_count, total_count, duplicate_count = insert_filtered_data(table, filtered_data, stations)
            total_success_count += success_count
            total_total_count += total_count
            total_duplicate_count += duplicate_count

        logger.info(f"Done! Inserted {total_success_count}/{total_total_count} records into {table} with {total_duplicate_count} duplicates")


def filter_data_for_date_range(data: pd.DataFrame, start_datetime: datetime, end_datetime: datetime) -> pd.DataFrame:
    """
    Filter data for a specific date range.
    
    Args:
        data (pd.DataFrame): Raw data from HTML
        start_datetime (datetime): Start datetime (inclusive)
        end_datetime (datetime): End datetime (inclusive)
        
    Returns:
        pd.DataFrame: Filtered data for the specified date range
    """
    filtered_rows = []
    
    for _, row in data.iterrows():
        # Parse the date and hour from the data
        fecha_str = row.iloc[0]  # Format: DD-MM-YYYY
        hora = row.iloc[1]  # Hour (1-24 format)
        
        # Convert to datetime
        fecha_parts = fecha_str.split('-')
        day = int(fecha_parts[0])
        month = int(fecha_parts[1])
        year = int(fecha_parts[2])
        
        # Convert hour from 1-24 to 0-23 format
        hour = hora - 1
        
        row_datetime = datetime(year, month, day, hour)
        
        # Check if this row is within our date range
        if start_datetime <= row_datetime <= end_datetime:
            filtered_rows.append(row)
    
    if filtered_rows:
        return pd.DataFrame(filtered_rows).reset_index(drop=True)
    else:
        return pd.DataFrame()


def insert_filtered_data(table: str, filtered_data: pd.DataFrame, stations: pd.Index) -> tuple[int, int]:
    """
    Insert filtered data into the database.
    
    Args:
        table (str): Table name to insert into
        filtered_data (pd.DataFrame): Data to insert
        stations (pd.Index): Station names
        
    Returns:
        tuple[int, int]: (success_count, total_count)
    """
    success_count = 0
    total_count = 0
    duplicate_count = 0
    
    for row_id in range(len(filtered_data)):
        row = filtered_data.iloc[row_id]
        
        # Parse date and hour
        fecha_split = row.iloc[0].split('-')  # DD-MM-YYYY
        hour = row.iloc[1] - 1  # Convert from 1-24 to 0-23 format
        
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
                    
                output = insert_data(table, fecha, str(stations[col_id]), str(value_native))
                if output == 'duplicate':
                    duplicate_count += 1
                else:
                    success_count += 1
    
    return success_count, total_count, duplicate_count


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
