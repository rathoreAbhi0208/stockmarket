import pandas as pd
import numpy as np
from typing import List
from models import Condition

def evaluate_operator(series1, operator, series2):
    """Evaluate comparison between two series or series and value"""
    if operator == '>':
        return series1 > series2
    elif operator == '<':
        return series1 < series2
    elif operator == '>=':
        return series1 >= series2
    elif operator == '<=':
        return series1 <= series2
    elif operator == '==':
        return series1 == series2
    elif operator == 'crosses_above':
        return (series1.shift(1) <= series2.shift(1)) & (series1 > series2)
    elif operator == 'crosses_below':
        return (series1.shift(1) >= series2.shift(1)) & (series1 < series2)
    else:
        raise ValueError(f"Unsupported operator: {operator}")

def evaluate_conditions(df, conditions: List[Condition]):
    """Evaluate a list of conditions and return boolean series"""
    if not conditions:
        return pd.Series([False] * len(df), index=df.index)
    
    results = []
    
    for condition in conditions:
        indicator_name = condition.indicator.upper()
        
        # Check if indicator exists
        if indicator_name not in df.columns:
            available = ', '.join([col for col in df.columns if not col.startswith('_')])
            raise ValueError(f"Indicator '{indicator_name}' not found. Available: {available}")
        
        series1 = df[indicator_name]
        
        # Determine if value is another indicator or a number
        if isinstance(condition.value, str):
            value_upper = condition.value.upper()
            if value_upper not in df.columns:
                raise ValueError(f"Indicator '{value_upper}' not found")
            series2 = df[value_upper]
        else:
            series2 = float(condition.value)
        
        # Evaluate the condition
        result = evaluate_operator(series1, condition.operator, series2)
        results.append(result)
    
    # Combine all conditions with AND logic
    combined = results[0]
    for result in results[1:]:
        combined = combined & result
    
    return combined

def evaluate_15m_strategy(df):
    """15-Minute Timeframe Strategy"""
    df = df.copy()
    df['Signal_15m'] = 'HOLD'
    df['Pass_15m'] = False
    
    close_above_ema200 = df['CLOSE'] > df['EMA_200']
    close_below_ema200 = df['CLOSE'] < df['EMA_200']
    
    ema_cross_up = (df['EMA_5'].shift(1) <= df['EMA_50'].shift(1)) & (df['EMA_5'] > df['EMA_50'])
    ema_cross_down = (df['EMA_5'].shift(1) >= df['EMA_50'].shift(1)) & (df['EMA_5'] < df['EMA_50'])
    
    stoch_buy_signal = df['STOCH_CROSS'] == 1
    stoch_sell_signal = df['STOCH_CROSS'] == -1
    
    buy_conditions = close_above_ema200 & ema_cross_up & stoch_buy_signal
    sell_conditions = close_below_ema200 & ema_cross_down & stoch_sell_signal
    
    df.loc[buy_conditions, 'Signal_15m'] = 'BUY'
    df.loc[sell_conditions, 'Signal_15m'] = 'SELL'
    df.loc[buy_conditions | sell_conditions, 'Pass_15m'] = True
    
    return df

def evaluate_5m_strategy(df):
    """5-Minute Timeframe Strategy"""
    df = df.copy()
    df['Signal_5m'] = 'HOLD'
    df['Pass_5m'] = False
    
    rsi_above_60 = df['RSI'] > 60
    rsi_below_40 = df['RSI'] < 40
    
    sma_cross_up = (df['SMA_9'].shift(1) <= df['SMA_50'].shift(1)) & (df['SMA_9'] > df['SMA_50'])
    sma_cross_down = (df['SMA_9'].shift(1) >= df['SMA_50'].shift(1)) & (df['SMA_9'] < df['SMA_50'])
    
    buy_conditions = sma_cross_up & rsi_above_60
    sell_conditions = sma_cross_down & rsi_below_40
    
    df.loc[buy_conditions, 'Signal_5m'] = 'BUY'
    df.loc[sell_conditions, 'Signal_5m'] = 'SELL'
    df.loc[buy_conditions | sell_conditions, 'Pass_5m'] = True
    
    return df

def evaluate_3m_strategy(df):
    """3-Minute Timeframe Strategy"""
    df = df.copy()
    df['Signal_3m'] = 'HOLD'
    df['Pass_3m'] = False
    
    ema_cross_up = (df['EMA_5'].shift(1) <= df['EMA_9'].shift(1)) & (df['EMA_5'] > df['EMA_9'])
    ema_cross_down = (df['EMA_5'].shift(1) >= df['EMA_9'].shift(1)) & (df['EMA_5'] < df['EMA_9'])
    
    macd_buy = (df['MACD'] > df['SIGNAL_LINE']) & (df['MACD_HIST'] > 0)
    macd_sell = (df['MACD'] < df['SIGNAL_LINE']) & (df['MACD_HIST'] < 0)
    
    ha_bullish = df['HA_CLOSE'] > df['HA_OPEN']
    ha_bearish = df['HA_CLOSE'] < df['HA_OPEN']
    
    buy_conditions = ema_cross_up & macd_buy & ha_bullish
    sell_conditions = ema_cross_down & macd_sell & ha_bearish
    
    df.loc[buy_conditions, 'Signal_3m'] = 'BUY'
    df.loc[sell_conditions, 'Signal_3m'] = 'SELL'
    df.loc[buy_conditions | sell_conditions, 'Pass_3m'] = True
    
    return df

def evaluate_multi_timeframe_conditions(df, conditions, timeframes_list):
    """
    Evaluate conditions across multiple timeframes
    
    Args:
        df: Combined DataFrame with indicators from multiple timeframes
        conditions: List of Condition objects with timeframe specifications
        timeframes_list: List of all timeframes being used
        
    Returns:
        Boolean Series indicating which rows meet all conditions
    """
    if not conditions:
        return pd.Series([False] * len(df), index=df.index)
    
    # Get the base timeframe (minimum)
    base_tf = min(timeframes_list)
    
    # Group conditions by timeframe
    conditions_by_tf = {}
    for condition in conditions:
        tf = condition.timeframe if condition.timeframe else base_tf
        if tf not in conditions_by_tf:
            conditions_by_tf[tf] = []
        conditions_by_tf[tf].append(condition)
    
    # Evaluate each timeframe's conditions
    all_results = pd.Series([True] * len(df), index=df.index)
    
    for tf, tf_conditions in conditions_by_tf.items():
        # Create modified conditions with timeframe suffix for column lookup
        modified_conditions = []
        for cond in tf_conditions:
            # Only add suffix if this is NOT the base timeframe and we have multiple timeframes
            if len(timeframes_list) > 1 and tf != base_tf:
                suffix = f"_{tf}"  # Changed from f"_{tf}m" to f"_{tf}"
                modified_conditions.append({
                    'original': cond,
                    'suffix': suffix
                })
            else:
                modified_conditions.append({
                    'original': cond,
                    'suffix': ''
                })
        
        # Evaluate conditions for this timeframe
        tf_result = evaluate_conditions_with_suffix(df, modified_conditions)
        all_results &= tf_result
    
    return all_results


def evaluate_conditions_with_suffix(df, modified_conditions):
    """
    Helper function to evaluate conditions with timeframe suffixes
    """
    if not modified_conditions:
        return pd.Series([False] * len(df), index=df.index)
    
    results = []
    
    for cond_info in modified_conditions:
        condition = cond_info['original']
        suffix = cond_info['suffix']
        
        indicator_col = condition.indicator.upper() + suffix
        
        if indicator_col not in df.columns:
            # Debug: print available columns
            available_cols = [col for col in df.columns if not col.startswith('_')]
            raise ValueError(
                f"Indicator {indicator_col} not found in data. "
                f"Available columns: {', '.join(available_cols[:20])}"
            )
        
        # Handle value - could be a number or another indicator
        if isinstance(condition.value, str):
            value_col = condition.value.upper() + suffix
            if value_col not in df.columns:
                available_cols = [col for col in df.columns if not col.startswith('_')]
                raise ValueError(
                    f"Value indicator {value_col} not found in data. "
                    f"Available columns: {', '.join(available_cols[:20])}"
                )
            comparison_value = df[value_col]
        else:
            comparison_value = condition.value
        
        # Perform comparison based on operator
        indicator_series = df[indicator_col]
        operator = condition.operator
        
        if operator == '>':
            result = indicator_series > comparison_value
        elif operator == '<':
            result = indicator_series < comparison_value
        elif operator == '>=':
            result = indicator_series >= comparison_value
        elif operator == '<=':
            result = indicator_series <= comparison_value
        elif operator == '==':
            result = indicator_series == comparison_value
        elif operator == 'crosses_above':
            # Current value > comparison AND previous value <= comparison
            if isinstance(comparison_value, pd.Series):
                result = (indicator_series > comparison_value) & (indicator_series.shift(1) <= comparison_value.shift(1))
            else:
                result = (indicator_series > comparison_value) & (indicator_series.shift(1) <= comparison_value)
        elif operator == 'crosses_below':
            # Current value < comparison AND previous value >= comparison
            if isinstance(comparison_value, pd.Series):
                result = (indicator_series < comparison_value) & (indicator_series.shift(1) >= comparison_value.shift(1))
            else:
                result = (indicator_series < comparison_value) & (indicator_series.shift(1) >= comparison_value)
        else:
            raise ValueError(f"Unknown operator: {operator}")
        
        results.append(result)
    
    # Combine all conditions with AND logic
    final_result = results[0]
    for result in results[1:]:
        final_result &= result
    
    return final_result