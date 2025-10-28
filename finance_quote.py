#!/usr/bin/env python3
"""

Requirements implemented:
- Takes a stock symbol as input (loop so user can enter multiple symbols)
- Prints current local date & time
- Prints full company name and ticker in parentheses
- Prints latest price, absolute change (with + / -), and percentage change (with + / -)
- Handles invalid symbols, network issues, and other errors gracefully

Dependency: yfinance
Install:    pip install yfinance --upgrade
"""

from __future__ import annotations

import sys
import time
from datetime import datetime
from typing import Optional, Tuple

# Third-party (install with: pip install yfinance)
import yfinance as yf
import pandas as pd


def _now_str() -> str:
    return datetime.now().strftime("%a %b %d %H:%M:%S %Z %Y")


def _format_change(curr: float, prev: float) -> Tuple[str, str]:
    delta = curr - prev
    pct = (delta / prev) * 100 if prev not in (0, None) else float("nan")

    
    sign_abs = "+" if delta > 0 else "-" if delta < 0 else ""
    sign_pct = "+" if pct > 0 else "-" if pct < 0 else ""

    abs_str = f"{sign_abs}{abs(delta):.2f}"
    pct_str = f"{sign_pct}{abs(pct):.2f}%"
    return abs_str, pct_str


def _get_company_name(ticker: yf.Ticker) -> Optional[str]:
    name_candidates = []

    
    try:
        info = ticker.get_info() or {}
        for key in ("longName", "shortName", "displayName", "quoteType"):
            if key in info and isinstance(info[key], str) and info[key].strip():
                name_candidates.append(info[key].strip())
    except Exception:
        pass

    
    return name_candidates[0] if name_candidates else None


def _latest_price_and_prev_close(symbol: str) -> Tuple[float, float]:
   
    try:
        intraday = yf.download(symbol, period="5d", interval="1m", progress=False, threads=False)
    
        if isinstance(intraday, pd.DataFrame) and not intraday.empty:
            intraday_close = intraday["Close"].dropna()
            if not intraday_close.empty:
                current = float(intraday_close.iloc[-1])
                tkr = yf.Ticker(symbol)
                prev_close = None
                try:
                    fi = tkr.fast_info
                    prev_close = float(fi.get("previousClose")) if fi and fi.get("previousClose") else None
                except Exception:
                    prev_close = None

                if prev_close is None:
                    daily = yf.download(symbol, period="5d", interval="1d", progress=False, threads=False)
                    if isinstance(daily, pd.DataFrame) and len(daily) >= 2:
                        prev_close = float(daily["Close"].dropna().iloc[-2])

                if prev_close is None or prev_close == 0:
                    raise ValueError("Could not determine previous close for change calculation.")

                return current, prev_close
    except Exception:
        
        pass

    
    daily = yf.download(symbol, period="2d", interval="1d", progress=False, threads=False)
    if not isinstance(daily, pd.DataFrame) or daily.empty or daily["Close"].dropna().empty:
        raise ValueError("No price data returned. The symbol may be invalid.")
    closes = daily["Close"].dropna()
    if len(closes) == 1:
        
        current = float(closes.iloc[-1])
        prev_close = float(closes.iloc[-1])
    else:
        current = float(closes.iloc[-1])
        prev_close = float(closes.iloc[-2])
    return current, prev_close


def quote(symbol: str) -> Tuple[str, str]:
    
    symbol = symbol.strip().upper()
    if not symbol:
        raise ValueError("Empty symbol.")

    current, prev_close = _latest_price_and_prev_close(symbol)

    
    tkr = yf.Ticker(symbol)
    name = _get_company_name(tkr) or symbol

    
    abs_change, pct_change = _format_change(current, prev_close)

    header = _now_str()
    name_line = f"{name} ({symbol})"
    quote_line = f"{current:.2f} {abs_change} ({pct_change})"

    return f"{header}\n{name_line}", quote_line


def main() -> int:
    print("Python Finance Info — using Yahoo Finance via yfinance")
    print("Tip: press Ctrl+C or Enter on an empty line to exit.\n")

    while True:
        try:
            user_in = input("Please enter a symbol:\n").strip()
            if user_in == "":
                print("Goodbye!")
                return 0

            header, quote_line = quote(user_in)
            print()  
            print(header)
            print(quote_line)
            print()  

        except KeyboardInterrupt:
            print("\nGoodbye!")
            return 0
        except ValueError as ve:
            print(f"Error: {ve}")
            print("Try again (e.g., AAPL, MSFT, NVDA).")
            print()
        except Exception as ex:
            # Network or unexpected errors
            print(f"Unexpected error: {ex.__class__.__name__}: {ex}")
            print("Check your network connection and try again.")
            print()
            # Small delay to avoid hammering in case of repeated failures
            time.sleep(0.5)


if __name__ == "__main__":
    sys.exit(main())
