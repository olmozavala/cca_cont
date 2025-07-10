import psycopg2
import netrc
from typing import Tuple
from sqlalchemy import create_engine

DB_MACHINE = 'DB-OZ'
DB_NAME = 'contingencia'
DB_HOST = 'amate.atmosfera.unam.mx'

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


def get_db_connection() -> psycopg2.extensions.connection:
    """
    Establish and return a psycopg2 connection to the database using .netrc credentials.

    Returns:
        psycopg2.extensions.connection: Database connection object.
    """
    user, password, host = get_db_credentials()
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=user,
        password=password,
        host=host
    )
    return conn


def get_db_engine():
    """Create a database engine using SQLAlchemy from psycopg2 connection."""
    try:
        conn = get_db_connection()
        # Create SQLAlchemy engine from the connection string
        connection_string = f"postgresql://{conn.info.user}:{conn.info.password}@{conn.info.host}:{conn.info.port}/{conn.info.dbname}"
        engine = create_engine(connection_string)
        return engine
    except Exception as e:
        print(f"Database connection error: {e}")
        return None
