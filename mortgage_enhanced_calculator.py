#!/usr/bin/env python3
"""
Enhanced Mortgage Refinance Calculator with Market Data Integration
Combines refinance analysis with real-time market data and expert forecasts
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

# Import our original calculator and market data scraper
from mortgage_refinance_calculator import MortgageRefinanceCalculator, MortgageDetails, RefinanceOptions
from mortgage_market_data import MortgageMarketDataScraper, RateData, MarketForecast

@dataclass
class MarketTiming:
    """Market timing analysis results"""
    current_rate_environment: str  # 'low', 'medium', 'high'
    forecast_consensus: str  # 'rates_rising', 'rates_falling', 'rates_stable'
    timing_recommendation: str  # 'refi_now', 'wait_3_months', 'wait_6_months', 'uncertain'
    confidence_score: float  # 0.0 to 1.0
    reasoning: str
    rate_outlook_3_months: str
    rate_outlook_6_months: str

class EnhancedMortgageCalculator:
    """Enhanced calculator with market data integration"""
    
    def __init__(self):
        self.calculator = MortgageRefinanceCalculator()
        self.market_scraper = MortgageMarketDataScraper()
        self.market_data = None
        self.market_timing = None
    
    def collect_market_data(self) -> Tuple[List[RateData], List[MarketForecast]]:
        """Collect current market data and forecasts"""
        print("🌐 Collecting real-time market data...")
        rates, forecasts = self.market_scraper.get_comprehensive_market_data()
        self.market_data = {'rates': rates, 'forecasts': forecasts}
        return rates, forecasts
    
    def analyze_market_timing(self) -> MarketTiming:
        """Analyze current market conditions for refinancing timing"""
        if not self.market_data:
            self.collect_market_data()
        
        rates = self.market_data['rates']
        forecasts = self.market_data['forecasts']
        
        # Get current rate environment
        current_30yr_rates = [r.rate for r in rates if '30-year' in r.rate_type.lower()]
        avg_current_rate = np.mean(current_30yr_rates) if current_30yr_rates else 0.07
        
        # Classify rate environment (based on historical context)
        if avg_current_rate < 0.055:  # Below 5.5%
            rate_environment = 'low'
        elif avg_current_rate < 0.075:  # Below 7.5%
            rate_environment = 'medium'
        else:
            rate_environment = 'high'
        
        # Analyze forecast consensus
        forecast_directions = [f.direction for f in forecasts]
        if not forecast_directions:
            forecast_consensus = 'uncertain'
        else:
            up_votes = forecast_directions.count('up')
            down_votes = forecast_directions.count('down')
            stable_votes = forecast_directions.count('stable')
            
            if up_votes > down_votes + stable_votes:
                forecast_consensus = 'rates_rising'
            elif down_votes > up_votes + stable_votes:
                forecast_consensus = 'rates_falling'
            else:
                forecast_consensus = 'rates_stable'
        
        # Generate timing recommendation
        timing_rec, confidence, reasoning, outlook_3m, outlook_6m = self._generate_timing_recommendation(
            rate_environment, forecast_consensus, avg_current_rate
        )
        
        self.market_timing = MarketTiming(
            current_rate_environment=rate_environment,
            forecast_consensus=forecast_consensus,
            timing_recommendation=timing_rec,
            confidence_score=confidence,
            reasoning=reasoning,
            rate_outlook_3_months=outlook_3m,
            rate_outlook_6_months=outlook_6m
        )
        
        return self.market_timing
    
    def _generate_timing_recommendation(self, rate_env: str, forecast: str, current_rate: float) -> Tuple[str, float, str, str, str]:
        """Generate timing recommendation based on market analysis"""
        
        if rate_env == 'low' and forecast == 'rates_rising':
            return (
                'refi_now',
                0.9,
                'Rates are currently low and expected to rise. Excellent time to refinance.',
                'Likely higher',
                'Likely higher'
            )
        elif rate_env == 'medium' and forecast == 'rates_rising':
            return (
                'refi_now',
                0.8,
                'Rates are moderate but trending up. Good time to lock in current rates.',
                'Likely higher',
                'Likely higher'
            )
        elif rate_env == 'high' and forecast == 'rates_falling':
            return (
                'wait_6_months',
                0.7,
                'Rates are high but may decline. Consider waiting for better opportunities.',
                'Possibly lower',
                'Likely lower'
            )
        elif rate_env == 'low' and forecast == 'rates_falling':
            return (
                'wait_3_months',
                0.6,
                'Rates are already low but may go lower. Short wait could be beneficial.',
                'Possibly lower',
                'Stable to lower'
            )
        elif forecast == 'rates_stable':
            return (
                'refi_now',
                0.7,
                'Rates appear stable. If refinancing makes sense financially, proceed.',
                'Stable',
                'Stable'
            )
        else:
            return (
                'uncertain',
                0.5,
                'Mixed market signals. Focus on personal financial benefits rather than timing.',
                'Uncertain',
                'Uncertain'
            )
    
    def enhanced_refinance_analysis(self, current_mortgage: MortgageDetails, 
                                   scenarios: List[Tuple[str, RefinanceOptions]],
                                   include_market_rates: bool = True) -> pd.DataFrame:
        """Enhanced analysis including market data and timing"""
        
        # Get market data if requested
        if include_market_rates:
            self.collect_market_data()
            market_timing = self.analyze_market_timing()
        
        # Run standard refinance analysis
        results_df = self.calculator.compare_scenarios(current_mortgage, scenarios)
        
        # Add market data if available
        if self.market_data and self.market_data['rates']:
            avg_rates = self.market_scraper.get_average_rates()
            current_market_30yr = avg_rates.get('30-year', current_mortgage.rate)
            current_market_15yr = avg_rates.get('15-year', current_mortgage.rate * 0.85)
            
            results_df['current_market_30yr'] = current_market_30yr * 100
            results_df['current_market_15yr'] = current_market_15yr * 100
            results_df['rate_vs_market_30yr'] = (results_df['effective_rate_after_buydown'] - current_market_30yr * 100)
        
        # Add market timing analysis
        if self.market_timing:
            results_df['market_timing_rec'] = self.market_timing.timing_recommendation
            results_df['market_confidence'] = self.market_timing.confidence_score
            results_df['rate_environment'] = self.market_timing.current_rate_environment
            results_df['forecast_consensus'] = self.market_timing.forecast_consensus
            
            # Enhanced recommendations considering market timing
            results_df['enhanced_recommendation'] = results_df.apply(
                lambda row: self._combine_recommendations(
                    row['recommendation'], 
                    self.market_timing.timing_recommendation,
                    row['break_even_years'] if isinstance(row['break_even_years'], (int, float)) else 999
                ), axis=1
            )
        
        return results_df
    
    def _combine_recommendations(self, financial_rec: str, timing_rec: str, break_even: float) -> str:
        """Combine financial and timing recommendations"""
        if 'NOT RECOMMENDED' in financial_rec:
            return financial_rec + " + Market timing irrelevant"
        
        if timing_rec == 'refi_now':
            if 'HIGHLY RECOMMENDED' in financial_rec:
                return "🔥 EXCELLENT OPPORTUNITY - Great financials + Perfect timing"
            else:
                return "⭐ GOOD OPPORTUNITY - " + financial_rec + " + Good market timing"
        elif timing_rec == 'wait_3_months':
            if break_even <= 2:
                return "⚡ REFI NOW - Benefits too good despite timing concerns"
            else:
                return "⏳ CONSIDER WAITING - " + financial_rec + " but rates may improve"
        elif timing_rec == 'wait_6_months':
            if break_even <= 1.5:
                return "⚡ REFI NOW - Exceptional benefits outweigh timing"
            else:
                return "⏳ WAIT FOR BETTER RATES - Market conditions suggest patience"
        else:
            return "🤔 MIXED SIGNALS - " + financial_rec + " but uncertain market"
    
    def generate_market_report(self) -> str:
        """Generate comprehensive market analysis report"""
        if not self.market_data or not self.market_timing:
            return "Market data not available. Run enhanced_refinance_analysis() first."
        
        rates = self.market_data['rates']
        forecasts = self.market_data['forecasts']
        timing = self.market_timing
        
        report = []
        report.append("🌐 MORTGAGE MARKET ANALYSIS REPORT")
        report.append("=" * 50)
        
        # Current rates section
        report.append(f"\n📊 CURRENT MARKET RATES:")
        if rates:
            avg_rates = self.market_scraper.get_average_rates()
            for rate_type, rate in avg_rates.items():
                report.append(f"  • {rate_type}: {rate*100:.3f}%")
            
            report.append(f"\n🏦 RATE SOURCES ({len(rates)} data points):")
            sources = list(set([r.source for r in rates]))
            for source in sources:
                source_rates = [r for r in rates if r.source == source]
                report.append(f"  • {source}: {len(source_rates)} rates")
        else:
            report.append("  No current rate data available")
        
        # Market timing analysis
        report.append(f"\n🎯 MARKET TIMING ANALYSIS:")
        report.append(f"  • Rate Environment: {timing.current_rate_environment.upper()}")
        report.append(f"  • Expert Consensus: {timing.forecast_consensus.replace('_', ' ').title()}")
        report.append(f"  • Timing Recommendation: {timing.timing_recommendation.replace('_', ' ').title()}")
        report.append(f"  • Confidence Level: {timing.confidence_score*100:.0f}%")
        report.append(f"  • 3-Month Outlook: {timing.rate_outlook_3_months}")
        report.append(f"  • 6-Month Outlook: {timing.rate_outlook_6_months}")
        
        # Expert forecasts
        report.append(f"\n🔮 EXPERT FORECASTS ({len(forecasts)} sources):")
        for forecast in forecasts:
            report.append(f"  • {forecast.source}: {forecast.direction.upper()} ({forecast.timeframe.replace('_', ' ')})")
            if forecast.confidence:
                report.append(f"    Confidence: {forecast.confidence}")
        
        # Market reasoning
        report.append(f"\n💡 MARKET REASONING:")
        report.append(f"  {timing.reasoning}")
        
        return "\n".join(report)
    
    def export_enhanced_analysis(self, filename: str = None) -> str:
        """Export enhanced analysis with market data"""
        if filename is None:
            filename = f"enhanced_mortgage_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Export main analysis
        main_filename = self.calculator.export_to_csv(filename)
        
        # Export market data
        market_filename = self.market_scraper.export_market_data(
            filename.replace('.csv', '_market_data.csv')
        )
        
        # Create summary file
        summary_filename = filename.replace('.csv', '_summary.txt')
        with open(summary_filename, 'w', encoding='utf-8') as f:
            f.write(self.generate_market_report())
        
        return main_filename, market_filename, summary_filename

def main():
    """Example usage of enhanced mortgage calculator"""
    
    print("🏠 ENHANCED MORTGAGE REFINANCE CALCULATOR WITH MARKET DATA")
    print("=" * 70)
    
    # Current mortgage example
    current_mortgage = MortgageDetails(
        rate=0.0675,  # 6.75%
        balance=450000,
        payment=3200,
        remaining_months=300
    )
    
    # Refinance scenarios
    scenarios = [
        ("Market Rate 30yr", RefinanceOptions(
            new_rate=0.0625,  # Will be updated with market data
            new_term_months=360,
            closing_costs=8000
        )),
        ("Market Rate + 1 Point", RefinanceOptions(
            new_rate=0.0625,
            new_term_months=360,
            closing_costs=8000,
            buydown_points=1.0
        )),
        ("15yr Market Rate", RefinanceOptions(
            new_rate=0.0575,  # Will be updated with market data
            new_term_months=180,
            closing_costs=8000
        ))
    ]
    
    # Run enhanced analysis
    enhanced_calc = EnhancedMortgageCalculator()
    results_df = enhanced_calc.enhanced_refinance_analysis(current_mortgage, scenarios)
    
    # Display market report
    print(enhanced_calc.generate_market_report())
    print("\n" + "=" * 70)
    
    # Display enhanced recommendations
    print(f"\n🎯 ENHANCED REFINANCE RECOMMENDATIONS:")
    for _, row in results_df.iterrows():
        print(f"\n📊 {row['custom_scenario_name']}")
        if 'enhanced_recommendation' in row:
            print(f"   {row['enhanced_recommendation']}")
        else:
            print(f"   {row['recommendation']}")
        
        if 'rate_vs_market_30yr' in row:
            market_diff = row['rate_vs_market_30yr']
            if abs(market_diff) < 0.01:
                market_note = "At market rate"
            elif market_diff > 0:
                market_note = f"{market_diff:.3f}% above market"
            else:
                market_note = f"{abs(market_diff):.3f}% below market"
            print(f"   Market Comparison: {market_note}")
    
    # Export results
    files = enhanced_calc.export_enhanced_analysis()
    print(f"\n✅ Enhanced analysis exported to:")
    for file in files:
        print(f"   • {file}")
    
    return enhanced_calc, results_df

if __name__ == "__main__":
    calc, results = main()