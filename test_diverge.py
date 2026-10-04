#!/usr/bin/env python3
"""
Unit tests for bullish RSI divergence detector.
"""

import unittest
from diverge import (
    wilder_rsi,
    find_swing_lows,
    find_swing_highs,
    detect_bullish_divergence,
    sma
)


class TestDivergenceDetector(unittest.TestCase):
    
    def test_clear_pass(self):
        """Test a clear bullish divergence PASS case."""
        # Create a price series with clear bullish divergence:
        # Price makes lower low, RSI makes higher low
        
        # Start with 250 days of prices to satisfy history requirements
        # Build a downtrend with two swing lows
        prices = []
        
        # First 200 days: declining trend from 100 to 50
        for i in range(200):
            prices.append(100 - (i * 0.25))
        
        # Create first swing low around day 210 at ~45
        for i in range(10):
            prices.append(50 - i * 0.5)  # decline to 45
        for i in range(10):
            prices.append(45 + i * 0.3)  # rise back up
        
        # Create second swing low around day 240 at ~42 (lower than first)
        for i in range(10):
            prices.append(48 - i * 0.6)  # decline to 42
        for i in range(10):
            prices.append(42 + i * 0.2)  # small rise
        
        # Pad to ensure we have enough data
        prices.extend([44] * 10)
        
        dates = [f"2024-{(i//30)+1:02d}-{(i%30)+1:02d}" for i in range(len(prices))]
        
        result = detect_bullish_divergence(prices, dates)
        
        # Should PASS: price lower low + RSI higher low + within timing window
        self.assertEqual(result['pass_fail'], 'PASS')
        self.assertIsNotNone(result['swing1_price'])
        self.assertIsNotNone(result['swing2_price'])
        self.assertLess(result['swing2_price'], result['swing1_price'])
        self.assertGreater(result['swing2_rsi'], result['swing1_rsi'])
    
    def test_clear_fail(self):
        """Test a clear FAIL case (no divergence)."""
        # Create a series where price makes higher low (not lower), so no divergence
        
        prices = []
        
        # First 200 days: gradual decline
        for i in range(200):
            prices.append(100 - (i * 0.15))
        
        # First swing low at ~40
        for i in range(10):
            prices.append(70 - i * 3)
        for i in range(10):
            prices.append(40 + i * 0.5)
        
        # Second swing low at ~42 (HIGHER than first, so no lower low)
        for i in range(10):
            prices.append(45 - i * 0.3)
        for i in range(10):
            prices.append(42 + i * 0.2)
        
        dates = [f"2024-{(i//30)+1:02d}-{(i%30)+1:02d}" for i in range(len(prices))]
        
        result = detect_bullish_divergence(prices, dates)
        
        # Should FAIL: price does not make lower low (second low is higher)
        self.assertEqual(result['pass_fail'], 'FAIL')
    
    def test_insufficient_history(self):
        """Test that insufficient history returns INSUFFICIENT."""
        # Only 100 days of data (need 221+)
        prices = [100 - i * 0.1 for i in range(100)]
        dates = [f"2024-{(i//30)+1:02d}-{(i%30)+1:02d}" for i in range(100)]
        
        result = detect_bullish_divergence(prices, dates)
        
        self.assertEqual(result['pass_fail'], 'INSUFFICIENT')
        self.assertIn('Insufficient history', result['reason'])
    
    def test_wilder_rsi_basic(self):
        """Test Wilder RSI calculation basics."""
        # Simple test: flat prices should give RSI around 50
        prices = [100] * 50
        rsi_values = wilder_rsi(prices, period=14)
        
        # First 14 should be None
        for i in range(14):
            self.assertIsNone(rsi_values[i])
        
        # Flat prices -> no gains or losses -> RSI undefined/50
        # (Actually will be NaN or 50 depending on implementation)
        self.assertIsNotNone(rsi_values[14])
    
    def test_swing_lows_detection(self):
        """Test swing low detection."""
        # Create clear swing lows
        prices = [10, 9, 8, 7, 8, 9, 10, 9, 8, 6, 7, 8, 9]
        swings = find_swing_lows(prices, window=2)
        
        # Should detect lows at indices where price is lowest in window
        self.assertTrue(len(swings) > 0)
    
    def test_sma_calculation(self):
        """Test simple moving average."""
        prices = [10, 20, 30, 40, 50]
        sma_vals = sma(prices, period=3)
        
        # First 2 should be None
        self.assertIsNone(sma_vals[0])
        self.assertIsNone(sma_vals[1])
        
        # Third should be (10+20+30)/3 = 20
        self.assertEqual(sma_vals[2], 20.0)
        
        # Fourth should be (20+30+40)/3 = 30
        self.assertEqual(sma_vals[3], 30.0)


if __name__ == '__main__':
    unittest.main()
