import netrc
from typing import Tuple, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
import pandas as pd

DB_MACHINE = 'DB-OZ'
# DB_MACHINE = 'DB-SOLOREAD'
# DB_MACHINE = 'OWGIS-OPERATIVO'
DB_NAME = 'contingencia'
DB_HOST = 'localhost'  # Changed from 'amate.atmosfera.unam.mx' to 'localhost'

# Pollutant mapping based on the provided table names
POLLUTANT_MAPPING = {
    'co': 'Carbon monoxide (CO)',
    'no': 'Nitric oxide (NO)',
    'nox': 'Nitrogen oxides (NOₓ: NO + NO₂)',
    'pmdiez': 'Particulate matter ≤ 10 µm (PM₁₀)',
    'pmdoscinco': 'Particulate matter ≤ 2.5 µm (PM₂.₅)',
    'sodos': 'Carbon dioxide (CO₂)',
    'otres': 'Ozone (O₃)'
}

# Meteorology mapping based on the met_* tables
METEOROLOGY_MAPPING = {
    'pba': 'Atmospheric pressure (PBA)',
    'rh': 'Relative humidity (RH)',
    'tmp': 'Temperature (TMP)',
    'wdr': 'Wind direction (WDR)',
    'wsp': 'Wind speed (WSP)'
}


def get_db_credentials(machine: str = DB_MACHINE) -> Tuple[str, str, str]:
    """
    Retrieve database credentials from the .netrc file for the given machine.

    Args:
        machine (str): The machine name in .netrc.

    Returns:
        Tuple[str, str, str]: (username, password, host)
    """
    auth = netrc.netrc().authenticators(machine)
    if not auth:
        raise ValueError(f"No credentials found for machine {machine} in .netrc")
    return auth[0], auth[2], DB_HOST


def get_db_engine() -> Optional[Engine]:
    """
    Create and return a SQLAlchemy engine for database connections.

    Returns:
        Optional[Engine]: SQLAlchemy engine object or None if connection fails.
    """
    try:
        user, password, host = get_db_credentials()
        connection_string = f"postgresql://{user}:{password}@{host}/{DB_NAME}"
        engine = create_engine(connection_string, pool_pre_ping=True)
        return engine
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

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
    value_str = value_str.replace('μ', 'u')
    
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



def test_connection() -> bool:
    """
    Test the database connection by executing a simple query.
    
    Returns:
        bool: True if connection successful, False otherwise.
    """
    try:
        engine = get_db_engine()
        if engine is None:
            print("❌ Failed to create database engine")
            return False
        
        # Test connection with a simple query
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            result.fetchone()
        
        print("✅ Database connection successful")
        return True
        
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False


def main():
    """
    Main function to test database connection when run as script.
    """
    print("Testing database connection...")
    print(f"Host: {DB_HOST}")
    print(f"Database: {DB_NAME}")
    print(f"Machine: {DB_MACHINE}")
    print("-" * 50)
    
    success = test_connection()
    
    if success:
        print("\n🎉 Database connection test passed!")
        return 0
    else:
        print("\n💥 Database connection test failed!")
        return 1


if __name__ == '__main__':
    exit(main()) 