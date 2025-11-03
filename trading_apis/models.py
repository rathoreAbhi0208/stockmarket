from pydantic import BaseModel, Field
from typing import List, Optional

class Condition(BaseModel):
    """Single condition for strategy evaluation"""
    indicator: str = Field(..., description="Indicator name (e.g., RSI, MACD, BB_UPPER)")
    operator: str = Field(..., description="Comparison operator: >, <, >=, <=, ==, crosses_above, crosses_below")
    value: float | str = Field(..., description="Value to compare against (number or another indicator name)")
    timeframe: Optional[int] = Field(None, description="Timeframe in minutes for this indicator (e.g., 3, 5, 15). If not specified, uses the base interval")
    
    class Config:
        json_schema_extra = {
            "example": {
                "indicator": "RSI",
                "operator": ">",
                "value": 70,
                "timeframe": 15
            }
        }

class StrategyRequest(BaseModel):
    """Complete strategy request for custom strategy builder"""
    symbol: str = Field(..., description="Stock symbol (e.g., RELIANCE.NS)")
    interval: int = Field(default=5, description="Base timeframe in minutes (1, 3, 5, 15, 30, 60)")
    buy_rules: List[Condition] = Field(..., description="Conditions for BUY signal")
    sell_rules: List[Condition] = Field(..., description="Conditions for SELL signal")
    start_time: Optional[str] = Field(None, description="Start time 'YYYY-MM-DD HH:mm' IST")
    end_time: Optional[str] = Field(None, description="End time 'YYYY-MM-DD HH:mm' IST")