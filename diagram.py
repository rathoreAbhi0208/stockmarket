# plot_client.py
import requests
import pandas as pd
import matplotlib
matplotlib.use('Qt5Agg')  # Try Qt5Agg backend instead
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
import time  # Add time for display control

def plot_signals(symbol="AAPL", timeframes=[5, 15, 30]):
    """
    Fetches data from the stock indicator API and plots the closing price
    with BUY and SELL signals.
    """
    # --- 1. Fetch Data from the API ---
    # Ensure your FastAPI server is running at this address
    api_url = "http://127.0.0.1:8000/indicator"
    params = {
        "symbol": symbol,
        "timeframes": timeframes
    }

    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        
        # Print debug information
        print(f"API Response Status Code: {response.status_code}")
        print(f"API Response Headers: {response.headers}")
        
        # Print the first part of the response to debug
        print("\nAPI Response Preview:")
        print(response.text[:500] + "..." if len(response.text) > 500 else response.text)
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from API: {e}")
        return

    # --- 2. Process the Data ---
    api_data = response.json()
    data_list = api_data.get('data', [])
    if not data_list:
        print("No data received from API to plot.")
        return

    df = pd.DataFrame(data_list)
    
    # The timestamp is in the 'Date' column from the API
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
    # The timestamp is in the 'Datetime' column from the API
    if 'Datetime' in df.columns:
        df['Datetime'] = pd.to_datetime(df['Datetime'])
        df.set_index('Datetime', inplace=True)
    else:
        print("Warning: No datetime column found in the API response")
        print("Warning: No 'Datetime' column found in the API response. Cannot plot.")
        return

    # --- 3. Visualize the Data ---
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, ax = plt.subplots(figsize=(15, 7))

    # Plot the closing price
    ax.plot(df.index, df['Close'], label='Close Price', color='skyblue', linewidth=2)

    # Plot BUY signals
    buy_signals = df[df['Final_Signal'] == 'BUY']
    ax.scatter(buy_signals.index, buy_signals['Close'], label='BUY Signal', marker='^', color='green', s=150, zorder=5)

    # Plot SELL signals
    sell_signals = df[df['Final_Signal'] == 'SELL']
    ax.scatter(sell_signals.index, sell_signals['Close'], label='SELL Signal', marker='v', color='red', s=150, zorder=5)

    # --- Formatting the Plot ---
    ax.set_title(f'"{symbol}" Close Price and Trading Signals ({max(timeframes)}m View)', fontsize=16)
    ax.set_xlabel('Date and Time', fontsize=12)
    ax.set_ylabel('Price (USD)', fontsize=12)
    ax.legend(fontsize=10)
    
    # Format the x-axis to be readable
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    try:
        # Save the plot with absolute path
        save_path = os.path.join(os.getcwd(), 'stock_signals.png')
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"\nPlot has been saved at: {save_path}")
        
        # Display the plot
        plt.show(block=False)  # Non-blocking display
        print("Plot window should be visible now.")
        print("Close the plot window manually when done viewing.")
        
        # Keep the script running for a while to show the plot
        time.sleep(30)  # Keep window open for 30 seconds
        
    except Exception as e:
        print(f"Could not display plot window: {e}")
        print(f"Please check the saved image at: {save_path}")
    finally:
        plt.close('all')  # Clean up all plots


if __name__ == "__main__":
    # Make sure to install required libraries:
    # pip install requests pandas matplotlib
    
    # Run the plotting function with your desired symbol and timeframes
    plot_signals(symbol="AAPL", timeframes=[5, 15, 60])
