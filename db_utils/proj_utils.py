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