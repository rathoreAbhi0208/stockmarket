import pytz

# API Configuration
FMP_BASE_URL = "https://financialmodelingprep.com/api/v3/historical-chart"
FMP_API_KEY = "pNfPaAqCCLW5TIyeNfmbJ9CaocjvSfNb"

# Timezone
IST_TZ = pytz.timezone("Asia/Kolkata")

# Interval mapping for FMP API
INTERVAL_MAP = {
    1: "1min",
    3: "1min",   # Will resample to 3m
    5: "5min",
    15: "15min",
    30: "30min",
    60: "1hour"
}

# Available indicators list
AVAILABLE_INDICATORS = [
    "OPEN", "HIGH", "LOW", "CLOSE", "VOLUME",
    "EMA_5", "EMA_9", "EMA_12", "EMA_20", "EMA_26", "EMA_50", "EMA_200",
    "SMA_5", "SMA_9", "SMA_20", "SMA_50", "SMA_200",
    "RSI", "MACD", "SIGNAL_LINE", "MACD_HIST",
    "BB_UPPER", "BB_MIDDLE", "BB_LOWER", "BB_WIDTH",
    "STOCH_K", "STOCH_D", "ATR", "ADX", "PLUS_DI", "MINUS_DI",
    "VOLUME_SMA", "VOLUME_RATIO", "CHANGE_PCT",
    "HA_OPEN", "HA_HIGH", "HA_LOW", "HA_CLOSE"
]


# Available operators
AVAILABLE_OPERATORS = [">", "<", ">=", "<=", "==", "crosses_above", "crosses_below"]

