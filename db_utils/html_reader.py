import pandas as pd

def read_html(table: str, year: int, month: int) -> pd.DataFrame:
    """
    Read HTML data from the CDMX air quality API.
    
    Args:
        table (str): Table name
        year (int): Year
        month (int): Month
    """
    url = f"http://www.aire.cdmx.gob.mx/estadisticas-consultas/concentraciones/respuesta.php?qtipo=HORARIOS&parametro={table}&anio={year}&qmes={month}"
    print(f"Reading data from: {url}")

    # Try multiple encodings to handle character encoding issues
    encodings_to_try = ['cp1252', 'latin-1', 'iso-8859-1', 'utf-8', None]
    data = None

    for encoding in encodings_to_try:
        try:
            if encoding:
                all_read = pd.read_html(url, header=1, encoding=encoding)
            else:
                all_read = pd.read_html(url, header=1)
            data = all_read[0]
            print(f"✅ Successfully read data with encoding: {encoding or 'default'} for table {table}")
            break
        except Exception as e:
            print(f"⚠️  Failed to load html with encoding {encoding or 'default'}: {str(e)[:100]}...")
            continue

    return data, url