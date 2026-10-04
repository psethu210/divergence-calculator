# Bullish RSI Divergence Detector

A Python command-line tool that detects bullish RSI divergence patterns in US stock prices. This is research tooling only and does not place trades or connect to brokers.

## What It Does

The tool analyzes price history and identifies bullish divergence signals based on these rules:

1. Price makes a lower low on the last two clear swing lows.
2. Wilder RSI(21) makes a higher low on those same two swing dates.
3. The second swing low is within the last 15 trading days OR the latest close is below the 200-day simple moving average.

A bearish divergence (price higher high and RSI lower high) automatically fails.

## Output Metrics

For each ticker, the tool computes and displays:

- PASS or FAIL result
- The two swing low dates with prices and RSI values
- 200-day simple moving average
- Percent below/above the 200-day average
- 20-day momentum (today's close minus close 20 sessions ago)
- Latest Wilder RSI(21)

## Installation

Requires Python 3.6 or later. No external dependencies needed (uses only standard library).

## Usage

Analyze a stock ticker (downloads data from Yahoo Finance):

```bash
python diverge.py TPL
```

Analyze a CSV file with date and close columns:

```bash
python diverge.py --csv prices.csv
```

CSV format should have a header row and two columns: date, close.

## Data Source

The tool downloads daily closing prices from Yahoo Finance public chart API. Data is fetched with a clear as-of date. No API keys required.

## Testing

Run the unit tests:

```bash
python test_diverge.py
```

Tests include three cases:
- One clear PASS with bullish divergence
- One clear FAIL without divergence
- One INSUFFICIENT case with too little history

## Technical Details

The tool uses Wilder's exponential smoothing method for RSI(21), not a simple average of up/down moves. Swing lows are detected as local minima with a 5-day window on each side.

Minimum history required: 221 trading days (for RSI calculation plus 200-day moving average).

## Example Output

```
Ticker: TPL
Data as of: 2024-01-15

Result: PASS
Reason: Bullish divergence: price lower low, RSI higher low

Swing Low 1: 2023-12-05
  Price: $245.30
  RSI(21): 28.45

Swing Low 2: 2024-01-08
  Price: $238.20
  RSI(21): 32.10

200-day SMA: $285.60
% vs SMA200: -16.60%
20-day Momentum: $-12.30
Latest RSI(21): 35.75
```

## Research Use Only

This tool is for research and analysis purposes only. It does not provide investment advice and does not execute trades.
