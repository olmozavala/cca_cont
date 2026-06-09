import atexit
import netrc
import os
import socket
import subprocess
import time
from typing import Optional, Tuple

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

DB_MACHINE = 'DB-OZ'
# DB_MACHINE = 'DB-SOLOREAD'
# DB_MACHINE = 'OWGIS-OPERATIVO'
DB_NAME = 'contingencia'
# On amate use 127.0.0.1:5432. SSH tunnel is only for remote machines.
DB_HOST = '127.0.0.1'
DB_PORT = 5432
DB_SSH_TARGET = os.environ.get('CCA_DB_SSH', 'amate')
DB_SSH_PORT = int(os.environ.get('CCA_DB_SSH_PORT', '5543'))
DB_SSH_LOCAL_PORT = int(os.environ.get('CCA_DB_LOCAL_PORT', '15432'))

_ssh_tunnel_proc: Optional[subprocess.Popen] = None

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
        machine: The machine name in .netrc.

    Returns:
        Tuple of username, password, and connection host (localhost via tunnel).
    """
    auth = netrc.netrc().authenticators(machine)
    if not auth:
        raise ValueError(f"No credentials found for machine {machine} in .netrc")
    return auth[0], auth[2], DB_HOST


def _use_ssh_tunnel() -> bool:
    """
    Return whether the DB connection should use an SSH port forward.

    Disabled by default on amate. Set CCA_DB_SSH_TUNNEL=1 for remote access.
    """
    if _is_local_amate():
        return False
    flag = os.environ.get('CCA_DB_SSH_TUNNEL', '0').lower()
    return flag in ('1', 'true', 'yes', 'on')


def _start_ssh_tunnel() -> Tuple[str, int]:
    """
    Open ssh -L local_port:127.0.0.1:5432 to amate (idempotent per process).

    Returns:
        Host and port for SQLAlchemy (127.0.0.1 and the local forward port).
    """
    global _ssh_tunnel_proc
    if _ssh_tunnel_proc is not None and _ssh_tunnel_proc.poll() is None:
        return '127.0.0.1', DB_SSH_LOCAL_PORT

    ssh_cmd = [
        'ssh',
        '-N',
        '-p',
        str(DB_SSH_PORT),
        '-L',
        f'{DB_SSH_LOCAL_PORT}:127.0.0.1:{DB_PORT}',
        DB_SSH_TARGET,
    ]
    _ssh_tunnel_proc = subprocess.Popen(
        ssh_cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    atexit.register(_stop_ssh_tunnel)
    time.sleep(1.5)
    if _ssh_tunnel_proc.poll() is not None:
        err = (
            _ssh_tunnel_proc.stderr.read().decode()
            if _ssh_tunnel_proc.stderr
            else ''
        )
        raise RuntimeError(f'SSH tunnel to {DB_SSH_TARGET} failed: {err}')
    return '127.0.0.1', DB_SSH_LOCAL_PORT


def _stop_ssh_tunnel() -> None:
    """Terminate the SSH tunnel subprocess if it is still running."""
    global _ssh_tunnel_proc
    if _ssh_tunnel_proc is not None and _ssh_tunnel_proc.poll() is None:
        _ssh_tunnel_proc.terminate()
        try:
            _ssh_tunnel_proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            _ssh_tunnel_proc.kill()
    _ssh_tunnel_proc = None


def _is_local_amate() -> bool:
    """
    Return whether this process is running on the amate database host.

    Cron jobs on amate should connect to PostgreSQL on 127.0.0.1 instead of
    opening an SSH tunnel to the same machine.

    Returns:
        True when the local hostname is amate.
    """
    hostname = socket.gethostname()
    return hostname == 'amate' or hostname.startswith('amate.')


def get_db_connect_host_port() -> Tuple[str, int]:
    """
    Resolve database host and port for PostgreSQL.

    On amate connects to 127.0.0.1:5432. Remote hosts may use an SSH tunnel
    (CCA_DB_SSH_TUNNEL=1) or direct amate.atmosfera.unam.mx:5432.

    Returns:
        Hostname and TCP port for PostgreSQL.
    """
    if _is_local_amate():
        return DB_HOST, DB_PORT
    if _use_ssh_tunnel():
        return _start_ssh_tunnel()
    return 'amate.atmosfera.unam.mx', DB_PORT


def get_db_engine() -> Optional[Engine]:
    """
    Create and return a SQLAlchemy engine for database connections.

    On amate uses local PostgreSQL at 127.0.0.1:5432.

    Returns:
        SQLAlchemy engine object or None if connection fails.
    """
    try:
        user, password, _ = get_db_credentials()
        host, port = get_db_connect_host_port()
        connection_string = (
            f"postgresql://{user}:{password}@{host}:{port}/{DB_NAME}"
        )
        engine = create_engine(
            connection_string,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 10},
        )
        return engine
    except Exception as e:
        print(f"Database connection error: {e}")
        return None


def clean_data_value(value: object) -> str:
    """
    Clean data values by removing special characters and converting to string.

    Args:
        value: Raw value from the data.

    Returns:
        Cleaned string value.
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
        num: Number to convert.

    Returns:
        Zero-padded string representation.
    """
    if num < 10:
        return "0" + str(num)
    else:
        return str(num)



def test_connection() -> bool:
    """
    Test the database connection by executing a simple query.

    Returns:
        True if connection successful, False otherwise.
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

        host, port = get_db_connect_host_port()
        print(f"✅ Database connection successful ({host}:{port})")
        return True

    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False


def main() -> int:
    """
    Main function to test database connection when run as script.

    Returns:
        Exit code 0 on success, 1 on failure.
    """
    print("Testing database connection...")
    host, port = get_db_connect_host_port()
    print(f"Connect: {host}:{port}")
    print(f"Database: {DB_NAME}")
    print(f"Machine: {DB_MACHINE}")
    if _is_local_amate():
        print("Mode: local PostgreSQL on amate")
    elif _use_ssh_tunnel():
        print(
            f"SSH tunnel: {DB_SSH_TARGET}:{DB_SSH_PORT} "
            f"-> 127.0.0.1:{DB_SSH_LOCAL_PORT}"
        )
    else:
        print(f"Mode: direct {DB_HOST}:{DB_PORT}")
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
