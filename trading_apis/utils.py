import pandas as pd
from datetime import timedelta
from config import IST_TZ

def parse_time_params(start_time: str, end_time: str):
    """Parse and validate time parameters"""
    if not (start_time and end_time):
        raise ValueError("Both start_time and end_time must be provided")
    
    start_dt = pd.Timestamp(start_time, tz=IST_TZ)
    end_dt = pd.Timestamp(end_time, tz=IST_TZ)
    
    if end_dt <= start_dt:
        raise ValueError("end_time must be after start_time")
    
    if (end_dt - start_dt) > timedelta(days=5):
        raise ValueError("Time range cannot exceed 5 days")
    
    return start_dt, end_dt