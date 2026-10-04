#!/usr/bin/env python3
"""
Bullish RSI divergence detector for US stocks.
Research tool only - does not place trades.
"""

import sys
import argparse
import urllib.request
import json
from datetime import datetime
from typing import List, Tuple, Optional


def wilder_rsi(prices: List[float], period: int = 21) -> List[Optional[float]]:
    """
    Calculate Wilder's RSI (exponential smoothing method).
    Returns list of RSI values, None for insufficient data points.
    """
    if len(prices) < period + 1:
        return [None] * len(prices)
    
    rsi_values = [None] * len(prices)
    changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    
    # First RSI calculation uses simple average
    gains = [max(c, 0) for c in changes[:period]]
    losses = [abs(min(c, 0)) for c in changes[:period]]
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    
    if avg_loss == 0:
        rsi_values[period] = 100.0
    else:
        rs = avg_gain / avg_loss
        rsi_values[period] = 100.0 - (100.0 / (1.0 + rs))
    
    # Subsequent RSI values use Wilder's exponential smoothing
    for i in range(period + 1, len(prices)):
        change = changes[i - 1]
        gain = max(change, 0)
        loss = abs(min(change, 0))
        
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
        
        if avg_loss == 0:
            rsi_values[i] = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi_values[i] = 100.0 - (100.0 / (1.0 + rs))
    
    return rsi_values


def find_swing_lows(prices: List[float], window: int = 5) -> List[int]:
    """
    Find swing low indices where price is lower than surrounding window.
    A swing low at index i means prices[i] is the minimum in [i-window, i+window].
    """
    swings = []
    for i in range(window, len(prices) - window):
        is_low = True
        for j in range(i - window, i + window + 1):
            if j != i and prices[j] <= prices[i]:
                is_low = False
                break
        if is_low:
            swings.append(i)
    return swings


def sma(prices: List[float], period: int) -> List[Optional[float]]:
    """Calculate simple moving average."""
    result = [None] * len(prices)
    for i in range(period - 1, len(prices)):
        result[i] = sum(prices[i - period + 1:i + 1]) / period
    return result


def detect_bullish_divergence(prices: List[float], dates: List[str]) -> dict:
    """
    Detect bullish RSI divergence according to locked rules.
    
    Returns dict with:
    - pass_fail: "PASS", "FAIL", or "INSUFFICIENT"
    - reason: explanation
    - swing1_date, swing1_price, swing1_rsi
    - swing2_date, swing2_price, swing2_rsi
    - sma200, pct_below_sma200
    - momentum_20d
    - latest_rsi
    """
    result = {
        'pass_fail': 'INSUFFICIENT',
        'reason': '',
        'swing1_date': None,
        'swing1_price': None,
        'swing1_rsi': None,
        'swing2_date': None,
        'swing2_price': None,
        'swing2_rsi': None,
        'sma200': None,
        'pct_below_sma200': None,
        'momentum_20d': None,
        'latest_rsi': None
    }
    
    # Need at least 221 days for RSI(21) + 200-day SMA
    if len(prices) < 221:
        result['reason'] = 'Insufficient history (need 221+ days)'
        return result
    
    # Calculate indicators
    rsi_values = wilder_rsi(prices, period=21)
    sma200_values = sma(prices, period=200)
    
    # Latest values
    latest_price = prices[-1]
    result['latest_rsi'] = rsi_values[-1]
    result['sma200'] = sma200_values[-1]
    
    if result['sma200'] is not None:
        result['pct_below_sma200'] = ((latest_price - result['sma200']) / result['sma200']) * 100
    
    # 20-day momentum
    if len(prices) >= 21:
        result['momentum_20d'] = prices[-1] - prices[-21]
    
    # Find swing lows
    swing_lows = find_swing_lows(prices)
    
    if len(swing_lows) < 2:
        result['reason'] = 'Need at least 2 swing lows'
        return result
    
    # Get last two swing lows
    swing1_idx = swing_lows[-2]
    swing2_idx = swing_lows[-1]
    
    result['swing1_date'] = dates[swing1_idx]
    result['swing1_price'] = prices[swing1_idx]
    result['swing1_rsi'] = rsi_values[swing1_idx]
    result['swing2_date'] = dates[swing2_idx]
    result['swing2_price'] = prices[swing2_idx]
    result['swing2_rsi'] = rsi_values[swing2_idx]
    
    # Check if RSI values are valid
    if result['swing1_rsi'] is None or result['swing2_rsi'] is None:
        result['reason'] = 'RSI not available at swing points'
        return result
    
    # Rule 1: Price makes lower low
    price_lower_low = result['swing2_price'] < result['swing1_price']
    
    # Rule 2: RSI makes higher low
    rsi_higher_low = result['swing2_rsi'] > result['swing1_rsi']
    
    # Rule 3: Timing condition
    days_since_swing2 = len(prices) - 1 - swing2_idx
    within_15_days = days_since_swing2 <= 15
    below_sma200 = result['pct_below_sma200'] is not None and result['pct_below_sma200'] < 0
    timing_ok = within_15_days or below_sma200
    
    # Check for bearish divergence (automatic FAIL)
    swing_highs = find_swing_highs(prices)
    if len(swing_highs) >= 2:
        high1_idx = swing_highs[-2]
        high2_idx = swing_highs[-1]
        if (prices[high2_idx] > prices[high1_idx] and 
            rsi_values[high2_idx] is not None and 
            rsi_values[high1_idx] is not None and
            rsi_values[high2_idx] < rsi_values[high1_idx]):
            result['pass_fail'] = 'FAIL'
            result['reason'] = 'Bearish divergence detected (price higher high, RSI lower high)'
            return result
    
    # Determine PASS or FAIL
    if price_lower_low and rsi_higher_low and timing_ok:
        result['pass_fail'] = 'PASS'
        result['reason'] = 'Bullish divergence: price lower low, RSI higher low'
    else:
        result['pass_fail'] = 'FAIL'
        reasons = []
        if not price_lower_low:
            reasons.append('price did not make lower low')
        if not rsi_higher_low:
            reasons.append('RSI did not make higher low')
        if not timing_ok:
            reasons.append('timing condition not met (>15 days and above SMA200)')
        result['reason'] = 'No bullish divergence: ' + ', '.join(reasons)
    
    return result


def find_swing_highs(prices: List[float], window: int = 5) -> List[int]:
    """Find swing high indices where price is higher than surrounding window."""
    swings = []
    for i in range(window, len(prices) - window):
        is_high = True
        for j in range(i - window, i + window + 1):
            if j != i and prices[j] >= prices[i]:
                is_high = False
                break
        if is_high:
            swings.append(i)
    return swings


def download_yahoo_data(ticker: str) -> Tuple[List[str], List[float], str]:
    """
    Download daily price data from Yahoo Finance chart API.
    Returns (dates, prices, as_of_date).
    """
    # Use Yahoo Finance chart API
    url = f'https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=2y'
    
    try:
        # Add user agent to avoid rate limiting
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
        
        chart = data['chart']['result'][0]
        timestamps = chart['timestamp']
        closes = chart['indicators']['quote'][0]['close']
        
        # Filter out None values
        dates = []
        prices = []
        for ts, close in zip(timestamps, closes):
            if close is not None:
                date_str = datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                dates.append(date_str)
                prices.append(float(close))
        
        as_of = datetime.now().strftime('%Y-%m-%d')
        return dates, prices, as_of
        
    except Exception as e:
        raise RuntimeError(f"Failed to download data for {ticker}: {e}")


def load_csv_data(filepath: str) -> Tuple[List[str], List[float]]:
    """
    Load price data from CSV file.
    Expected format: date,close (with header row).
    """
    dates = []
    prices = []
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            line = line.strip()
            if i == 0 or not line:
                continue  # Skip header
            parts = line.split(',')
            if len(parts) >= 2:
                dates.append(parts[0])
                prices.append(float(parts[1]))
    
    return dates, prices


def format_output(result: dict, ticker: str, as_of: str = None) -> str:
    """Format analysis result as plain text."""
    lines = []
    lines.append(f"Ticker: {ticker}")
    if as_of:
        lines.append(f"Data as of: {as_of}")
    lines.append(f"\nResult: {result['pass_fail']}")
    lines.append(f"Reason: {result['reason']}")
    
    if result['swing1_date']:
        lines.append(f"\nSwing Low 1: {result['swing1_date']}")
        lines.append(f"  Price: ${result['swing1_price']:.2f}")
        lines.append(f"  RSI(21): {result['swing1_rsi']:.2f}")
    
    if result['swing2_date']:
        lines.append(f"\nSwing Low 2: {result['swing2_date']}")
        lines.append(f"  Price: ${result['swing2_price']:.2f}")
        lines.append(f"  RSI(21): {result['swing2_rsi']:.2f}")
    
    if result['sma200'] is not None:
        lines.append(f"\n200-day SMA: ${result['sma200']:.2f}")
        lines.append(f"% vs SMA200: {result['pct_below_sma200']:+.2f}%")
    
    if result['momentum_20d'] is not None:
        lines.append(f"20-day Momentum: ${result['momentum_20d']:+.2f}")
    
    if result['latest_rsi'] is not None:
        lines.append(f"Latest RSI(21): {result['latest_rsi']:.2f}")
    
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Detect bullish RSI divergence in US stocks (research only)'
    )
    parser.add_argument('input', help='Stock ticker symbol or path to CSV file')
    parser.add_argument('--csv', action='store_true', help='Input is a CSV file')
    
    args = parser.parse_args()
    
    try:
        if args.csv:
            dates, prices = load_csv_data(args.input)
            as_of = None
            ticker = args.input
        else:
            dates, prices, as_of = download_yahoo_data(args.input)
            ticker = args.input
        
        result = detect_bullish_divergence(prices, dates)
        output = format_output(result, ticker, as_of)
        print(output)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
