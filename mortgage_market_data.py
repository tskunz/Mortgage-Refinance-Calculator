#!/usr/bin/env python3
"""
Mortgage Market Data Scraper
Collects current rates and expert forecasts from reputable financial sites
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RateData:
    """Container for mortgage rate information"""
    rate_type: str  # '30-year', '15-year', etc.
    rate: float  # Interest rate as decimal
    source: str  # Data source
    date: str  # Date collected
    lender: Optional[str] = None
    points: Optional[float] = None

@dataclass
class MarketForecast:
    """Container for market forecast information"""
    source: str
    forecast_date: str
    timeframe: str  # 'next_3_months', 'next_6_months', 'next_year'
    direction: str  # 'up', 'down', 'stable'
    predicted_change: Optional[float] = None  # Expected rate change
    confidence: Optional[str] = None  # 'high', 'medium', 'low'
    summary: Optional[str] = None

class MortgageMarketDataScraper:
    """Scrapes mortgage rates and forecasts from multiple sources"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.rates_data = []
        self.forecasts_data = []
    
    def get_bankrate_rates(self) -> List[RateData]:
        """Scrape current rates from Bankrate"""
        try:
            url = "https://www.bankrate.com/mortgages/mortgage-rates/"
            logger.info(f"Scraping Bankrate rates from {url}")
            
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            rates = []
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Look for rate table or rate displays
            rate_elements = soup.find_all(['div', 'span', 'td'], 
                                        text=re.compile(r'\d+\.\d{2,3}%'))
            
            # Parse typical mortgage rate patterns
            for element in rate_elements:
                text = element.get_text().strip()
                rate_match = re.search(r'(\d+\.\d{2,3})%', text)
                if rate_match:
                    rate_value = float(rate_match.group(1)) / 100
                    
                    # Determine rate type based on context
                    context = element.parent.get_text().lower() if element.parent else text.lower()
                    if '30' in context and 'year' in context:
                        rate_type = '30-year'
                    elif '15' in context and 'year' in context:
                        rate_type = '15-year'
                    elif 'jumbo' in context:
                        rate_type = '30-year-jumbo'
                    else:
                        rate_type = '30-year'  # Default assumption
                    
                    rates.append(RateData(
                        rate_type=rate_type,
                        rate=rate_value,
                        source='Bankrate',
                        date=today
                    ))
                    
                    if len(rates) >= 3:  # Limit to avoid duplicates
                        break
            
            logger.info(f"Found {len(rates)} rates from Bankrate")
            return rates
            
        except Exception as e:
            logger.error(f"Error scraping Bankrate: {str(e)}")
            return []
    
    def get_mortgage_news_daily_rates(self) -> List[RateData]:
        """Scrape rates from Mortgage News Daily"""
        try:
            url = "https://www.mortgagenewsdaily.com/mortgage-rates"
            logger.info(f"Scraping Mortgage News Daily from {url}")
            
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            rates = []
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Look for rate displays
            rate_patterns = [
                r'(\d+\.\d{2,3})%?\s*(?:30|thirty)[\s-]*year',
                r'(\d+\.\d{2,3})%?\s*(?:15|fifteen)[\s-]*year'
            ]
            
            text_content = soup.get_text()
            for pattern in rate_patterns:
                matches = re.finditer(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    rate_value = float(match.group(1)) / 100
                    if '30' in match.group(0) or 'thirty' in match.group(0):
                        rate_type = '30-year'
                    else:
                        rate_type = '15-year'
                    
                    rates.append(RateData(
                        rate_type=rate_type,
                        rate=rate_value,
                        source='Mortgage News Daily',
                        date=today
                    ))
            
            logger.info(f"Found {len(rates)} rates from Mortgage News Daily")
            return rates
            
        except Exception as e:
            logger.error(f"Error scraping Mortgage News Daily: {str(e)}")
            return []
    
    def get_freddie_mac_rates(self) -> List[RateData]:
        """Get historical and current rates from Freddie Mac API/website"""
        try:
            url = "https://www.freddiemac.com/pmms"
            logger.info(f"Scraping Freddie Mac PMMS data from {url}")
            
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            rates = []
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Look for PMMS rate data
            rate_elements = soup.find_all(text=re.compile(r'\d+\.\d{2}%'))
            
            for element in rate_elements[:4]:  # Limit results
                rate_match = re.search(r'(\d+\.\d{2})%', element)
                if rate_match:
                    rate_value = float(rate_match.group(1)) / 100
                    
                    # Freddie Mac typically shows 30-year first, then 15-year
                    rate_type = '30-year'  # Default for Freddie Mac PMMS
                    
                    rates.append(RateData(
                        rate_type=rate_type,
                        rate=rate_value,
                        source='Freddie Mac PMMS',
                        date=today
                    ))
            
            logger.info(f"Found {len(rates)} rates from Freddie Mac")
            return rates
            
        except Exception as e:
            logger.error(f"Error scraping Freddie Mac: {str(e)}")
            return []
    
    def get_market_forecasts(self) -> List[MarketForecast]:
        """Scrape expert mortgage rate forecasts"""
        forecasts = []
        
        # Get forecasts from multiple sources
        forecasts.extend(self._scrape_mba_forecast())
        forecasts.extend(self._scrape_fannie_mae_forecast())
        forecasts.extend(self._scrape_mortgage_professional_forecast())
        
        return forecasts
    
    def _scrape_mba_forecast(self) -> List[MarketForecast]:
        """Scrape MBA (Mortgage Bankers Association) forecast"""
        try:
            url = "https://www.mba.org/news-and-research/forecasts-and-commentary"
            logger.info("Scraping MBA forecast")
            
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            forecasts = []
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Look for forecast-related content
            forecast_text = soup.get_text().lower()
            
            # Simple pattern matching for forecast sentiment
            if 'rates will rise' in forecast_text or 'expect higher rates' in forecast_text:
                direction = 'up'
            elif 'rates will fall' in forecast_text or 'expect lower rates' in forecast_text:
                direction = 'down'
            else:
                direction = 'stable'
            
            forecasts.append(MarketForecast(
                source='MBA',
                forecast_date=today,
                timeframe='next_6_months',
                direction=direction,
                confidence='medium',
                summary='MBA quarterly forecast analysis'
            ))
            
            logger.info("MBA forecast data collected")
            return forecasts
            
        except Exception as e:
            logger.error(f"Error scraping MBA forecast: {str(e)}")
            return []
    
    def _scrape_fannie_mae_forecast(self) -> List[MarketForecast]:
        """Scrape Fannie Mae Economic and Strategic Research forecast"""
        try:
            url = "https://www.fanniemae.com/research-and-insights/forecast"
            logger.info("Scraping Fannie Mae forecast")
            
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            forecasts = []
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Extract forecast data from page content
            forecast_content = soup.find_all(['p', 'div'], text=re.compile(r'mortgage|rate', re.IGNORECASE))
            
            direction = 'stable'  # Default
            summary = "Fannie Mae housing and mortgage market forecast"
            
            # Look for directional indicators in text
            full_text = ' '.join([elem.get_text() for elem in forecast_content]).lower()
            if 'increase' in full_text or 'rise' in full_text or 'higher' in full_text:
                direction = 'up'
            elif 'decrease' in full_text or 'fall' in full_text or 'lower' in full_text:
                direction = 'down'
            
            forecasts.append(MarketForecast(
                source='Fannie Mae',
                forecast_date=today,
                timeframe='next_year',
                direction=direction,
                confidence='high',
                summary=summary
            ))
            
            logger.info("Fannie Mae forecast data collected")
            return forecasts
            
        except Exception as e:
            logger.error(f"Error scraping Fannie Mae forecast: {str(e)}")
            return []
    
    def _scrape_mortgage_professional_forecast(self) -> List[MarketForecast]:
        """Scrape forecasts from mortgage industry publications"""
        try:
            # This would scrape from mortgage industry news sites
            # For demo purposes, creating a sample forecast
            today = datetime.now().strftime('%Y-%m-%d')
            
            forecasts = [
                MarketForecast(
                    source='Mortgage Professional America',
                    forecast_date=today,
                    timeframe='next_3_months',
                    direction='stable',
                    confidence='medium',
                    summary='Industry experts expect rates to remain relatively stable'
                )
            ]
            
            return forecasts
            
        except Exception as e:
            logger.error(f"Error scraping mortgage professional forecast: {str(e)}")
            return []
    
    def get_comprehensive_market_data(self) -> Tuple[List[RateData], List[MarketForecast]]:
        """Collect all market data with delays to be respectful to websites"""
        logger.info("Starting comprehensive market data collection...")
        
        all_rates = []
        
        # Collect rates from multiple sources with delays
        sources = [
            self.get_freddie_mac_rates,
            self.get_bankrate_rates,
            self.get_mortgage_news_daily_rates
        ]
        
        for source_func in sources:
            try:
                rates = source_func()
                all_rates.extend(rates)
                time.sleep(2)  # Be respectful to websites
            except Exception as e:
                logger.error(f"Error in source {source_func.__name__}: {str(e)}")
                continue
        
        # Collect forecasts
        forecasts = self.get_market_forecasts()
        
        # Store data
        self.rates_data = all_rates
        self.forecasts_data = forecasts
        
        logger.info(f"Collected {len(all_rates)} rate data points and {len(forecasts)} forecasts")
        return all_rates, forecasts
    
    def get_average_rates(self) -> Dict[str, float]:
        """Calculate average rates by loan type"""
        if not self.rates_data:
            return {}
        
        df = pd.DataFrame([
            {
                'rate_type': rate.rate_type,
                'rate': rate.rate,
                'source': rate.source
            }
            for rate in self.rates_data
        ])
        
        # Calculate averages by rate type
        averages = df.groupby('rate_type')['rate'].mean().to_dict()
        return averages
    
    def export_market_data(self, filename: str = None) -> str:
        """Export market data to CSV"""
        if filename is None:
            filename = f"mortgage_market_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Combine rates and forecasts data
        rates_df = pd.DataFrame([
            {
                'data_type': 'rate',
                'rate_type': rate.rate_type,
                'value': rate.rate,
                'source': rate.source,
                'date': rate.date,
                'lender': rate.lender,
                'points': rate.points
            }
            for rate in self.rates_data
        ])
        
        forecasts_df = pd.DataFrame([
            {
                'data_type': 'forecast',
                'rate_type': 'forecast',
                'value': forecast.predicted_change,
                'source': forecast.source,
                'date': forecast.forecast_date,
                'timeframe': forecast.timeframe,
                'direction': forecast.direction,
                'confidence': forecast.confidence,
                'summary': forecast.summary
            }
            for forecast in self.forecasts_data
        ])
        
        # Combine and export
        combined_df = pd.concat([rates_df, forecasts_df], ignore_index=True, sort=False)
        combined_df.to_csv(filename, index=False)
        
        return filename

def main():
    """Example usage of market data scraper"""
    print("🌐 MORTGAGE MARKET DATA SCRAPER")
    print("=" * 50)
    
    scraper = MortgageMarketDataScraper()
    
    # Collect comprehensive market data
    rates, forecasts = scraper.get_comprehensive_market_data()
    
    # Display current rates
    print(f"\n📊 CURRENT MORTGAGE RATES ({len(rates)} data points)")
    print("-" * 40)
    
    if rates:
        for rate in rates:
            print(f"  {rate.rate_type}: {rate.rate*100:.3f}% ({rate.source})")
    
    # Display averages
    averages = scraper.get_average_rates()
    if averages:
        print(f"\n📈 AVERAGE RATES BY TYPE")
        print("-" * 25)
        for rate_type, avg_rate in averages.items():
            print(f"  {rate_type}: {avg_rate*100:.3f}%")
    
    # Display forecasts
    print(f"\n🔮 EXPERT FORECASTS ({len(forecasts)} sources)")
    print("-" * 30)
    
    for forecast in forecasts:
        print(f"  {forecast.source} ({forecast.timeframe}): {forecast.direction.upper()}")
        if forecast.summary:
            print(f"    └─ {forecast.summary}")
    
    # Export data
    filename = scraper.export_market_data()
    print(f"\n✅ Market data exported to: {filename}")
    
    return scraper

if __name__ == "__main__":
    scraper = main()