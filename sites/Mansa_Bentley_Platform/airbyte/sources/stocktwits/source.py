#!/usr/bin/env python3
"""
Airbyte Source Connector for Stocktwits Sentiment Data
Implements the Airbyte Protocol for streaming sentiment scores
"""
import sys
import json
import argparse
from datetime import datetime
from typing import Any, Dict, List
import requests
from bs4 import BeautifulSoup


class StocktwitsSource:
    """Airbyte source connector for Stocktwits sentiment data"""
    
    def __init__(self):
        self.name = "source-stocktwits-sentiment"
        self.version = "0.1.0"
    
    def spec(self) -> Dict[str, Any]:
        """Return the connector specification"""
        return {
            "documentationUrl": "https://stocktwits.com/developers/docs/api",
            "connectionSpecification": {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "title": "Stocktwits Sentiment Source Spec",
                "type": "object",
                "required": ["tickers"],
                "properties": {
                    "tickers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "title": "Stock Tickers",
                        "description": "List of stock tickers to fetch sentiment for (e.g., AMZN, TSLA, AAPL)",
                        "examples": [["AMZN", "TSLA", "AAPL"]]
                    },
                    "user_agent": {
                        "type": "string",
                        "title": "User Agent",
                        "description": "User agent for HTTP requests",
                        "default": "Mozilla/5.0 (compatible; AirbyteBot/1.0)"
                    }
                }
            }
        }
    
    def check(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test the connection configuration"""
        try:
            tickers = config.get("tickers", [])
            if not tickers:
                return {
                    "status": "FAILED",
                    "message": "No tickers provided in configuration"
                }
            
            # Test with first ticker
            test_ticker = tickers[0]
            user_agent = config.get("user_agent", "Mozilla/5.0")
            
            url = f"https://stocktwits.com/symbol/{test_ticker}"
            headers = {"User-Agent": user_agent}
            resp = requests.get(url, headers=headers, timeout=10)
            
            if resp.status_code == 200:
                return {
                    "status": "SUCCEEDED",
                    "message": f"Successfully connected to Stocktwits for {test_ticker}"
                }
            else:
                return {
                    "status": "FAILED",
                    "message": f"Failed to connect: HTTP {resp.status_code}"
                }
        except Exception as e:
            return {
                "status": "FAILED",
                "message": f"Connection test failed: {str(e)}"
            }
    
    def discover(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Return the catalog of available streams"""
        return {
            "streams": [
                {
                    "name": "sentiment_scores",
                    "json_schema": {
                        "$schema": "http://json-schema.org/draft-07/schema#",
                        "type": "object",
                        "properties": {
                            "ticker": {"type": "string"},
                            "sentiment_score": {"type": ["number", "null"]},
                            "bullish_count": {"type": ["integer", "null"]},
                            "bearish_count": {"type": ["integer", "null"]},
                            "total_messages": {"type": ["integer", "null"]},
                            "scraped_at": {"type": "string", "format": "date-time"},
                            "url": {"type": "string"}
                        }
                    },
                    "supported_sync_modes": ["full_refresh", "incremental"],
                    "source_defined_cursor": True,
                    "default_cursor_field": ["scraped_at"]
                }
            ]
        }
    
    def read(self, config: Dict[str, Any], catalog: Dict[str, Any], 
             state: Dict[str, Any] = None) -> None:
        """Read data from Stocktwits and emit records"""
        tickers = config.get("tickers", [])
        user_agent = config.get("user_agent", "Mozilla/5.0")
        
        for ticker in tickers:
            try:
                data = self._scrape_sentiment(ticker, user_agent)
                
                # Emit Airbyte record
                record = {
                    "type": "RECORD",
                    "record": {
                        "stream": "sentiment_scores",
                        "data": data,
                        "emitted_at": int(datetime.utcnow().timestamp() * 1000)
                    }
                }
                self._emit(record)
                
            except Exception as e:
                # Emit log message for errors
                log = {
                    "type": "LOG",
                    "log": {
                        "level": "ERROR",
                        "message": f"Failed to scrape {ticker}: {str(e)}"
                    }
                }
                self._emit(log)
        
        # Emit final state
        new_state = {
            "sentiment_scores": {
                "last_sync": datetime.utcnow().isoformat()
            }
        }
        self._emit({"type": "STATE", "state": {"data": new_state}})
    
    def _scrape_sentiment(self, ticker: str, user_agent: str) -> Dict[str, Any]:
        """Scrape sentiment data for a ticker"""
        url = f"https://stocktwits.com/symbol/{ticker}"
        headers = {"User-Agent": user_agent}
        
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Try to extract sentiment data
        # Note: Stocktwits structure may change, adjust selectors as needed
        sentiment_score = None
        bullish_count = None
        bearish_count = None
        total_messages = None
        
        # Look for sentiment indicators
        sentiment_elements = soup.find_all("span", class_="sentiment")
        for elem in sentiment_elements:
            text = elem.get_text().strip()
            if "Bullish" in text:
                try:
                    bullish_count = int(text.split()[1].replace(",", ""))
                except:
                    pass
            elif "Bearish" in text:
                try:
                    bearish_count = int(text.split()[1].replace(",", ""))
                except:
                    pass
        
        # Calculate sentiment score if we have counts
        if bullish_count is not None and bearish_count is not None:
            total = bullish_count + bearish_count
            if total > 0:
                sentiment_score = (bullish_count - bearish_count) / total
                total_messages = total
        
        return {
            "ticker": ticker,
            "sentiment_score": sentiment_score,
            "bullish_count": bullish_count,
            "bearish_count": bearish_count,
            "total_messages": total_messages,
            "scraped_at": datetime.utcnow().isoformat(),
            "url": url
        }
    
    def _emit(self, message: Dict[str, Any]) -> None:
        """Emit an Airbyte protocol message"""
        print(json.dumps(message), flush=True)


def main():
    """Main entry point for the Airbyte source"""
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["spec", "check", "discover", "read"])
    parser.add_argument("--config", type=str, help="Path to config file")
    parser.add_argument("--catalog", type=str, help="Path to catalog file")
    parser.add_argument("--state", type=str, help="Path to state file")
    
    args = parser.parse_args()
    source = StocktwitsSource()
    
    if args.command == "spec":
        print(json.dumps(source.spec()))
    
    elif args.command == "check":
        if not args.config:
            print(json.dumps({"status": "FAILED", "message": "Missing --config"}))
            sys.exit(1)
        
        with open(args.config, 'r') as f:
            config = json.load(f)
        
        print(json.dumps(source.check(config)))
    
    elif args.command == "discover":
        if not args.config:
            print(json.dumps({"status": "FAILED", "message": "Missing --config"}))
            sys.exit(1)
        
        with open(args.config, 'r') as f:
            config = json.load(f)
        
        print(json.dumps(source.discover(config)))
    
    elif args.command == "read":
        if not args.config or not args.catalog:
            print(json.dumps({
                "type": "LOG",
                "log": {
                    "level": "ERROR",
                    "message": "Missing --config or --catalog"
                }
            }))
            sys.exit(1)
        
        with open(args.config, 'r') as f:
            config = json.load(f)
        
        with open(args.catalog, 'r') as f:
            catalog = json.load(f)
        
        state = None
        if args.state:
            with open(args.state, 'r') as f:
                state = json.load(f)
        
        source.read(config, catalog, state)


if __name__ == "__main__":
    main()
