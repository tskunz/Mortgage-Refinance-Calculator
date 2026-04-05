#!/usr/bin/env python3
"""
Interactive Enhanced Mortgage Refinance Calculator
User-friendly prompts for mortgage details with market data integration
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import sys

# Import our enhanced calculator
from mortgage_enhanced_calculator import EnhancedMortgageCalculator
from mortgage_refinance_calculator import MortgageDetails, RefinanceOptions

class InteractiveMortgageCalculator:
    """Interactive interface for the enhanced mortgage calculator"""
    
    def __init__(self):
        self.calculator = EnhancedMortgageCalculator()
        self.current_mortgage = None
        self.scenarios = []
    
    def get_user_input(self, prompt: str, input_type: str = 'str', min_val: float = None, max_val: float = None, default=None) -> any:
        """Get validated user input"""
        while True:
            try:
                if default is not None:
                    user_input = input(f"{prompt} (default: {default}): ").strip()
                    if not user_input:
                        return default
                else:
                    user_input = input(f"{prompt}: ").strip()
                
                if input_type == 'str':
                    return user_input
                elif input_type == 'float':
                    value = float(user_input)
                    if min_val is not None and value < min_val:
                        print(f"❌ Value must be at least {min_val}")
                        continue
                    if max_val is not None and value > max_val:
                        print(f"❌ Value must be at most {max_val}")
                        continue
                    return value
                elif input_type == 'int':
                    value = int(user_input)
                    if min_val is not None and value < min_val:
                        print(f"❌ Value must be at least {min_val}")
                        continue
                    if max_val is not None and value > max_val:
                        print(f"❌ Value must be at most {max_val}")
                        continue
                    return value
                elif input_type == 'bool':
                    return user_input.lower() in ['y', 'yes', 'true', '1']
                
            except ValueError:
                print(f"❌ Please enter a valid {input_type}")
                continue
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                sys.exit(0)
    
    def get_current_mortgage_details(self) -> MortgageDetails:
        """Interactive input for current mortgage details"""
        print("\n" + "="*60)
        print("🏠 CURRENT MORTGAGE DETAILS")
        print("="*60)
        print("Please enter your current mortgage information:")
        print()
        
        # Current interest rate
        rate = self.get_user_input(
            "💰 Current interest rate (e.g., 6.75 for 6.75%)", 
            'float', 0.1, 20.0
        ) / 100
        
        # Outstanding balance
        balance = self.get_user_input(
            "💵 Outstanding mortgage balance (e.g., 450000 for $450,000)",
            'float', 1000, 10000000
        )
        
        # Current monthly payment
        payment = self.get_user_input(
            "📅 Current monthly payment - P&I only (e.g., 3200 for $3,200)",
            'float', 100, 50000
        )
        
        # Remaining term
        print("\n🕐 How much time is left on your current loan?")
        remaining_years = self.get_user_input(
            "   Years remaining (e.g., 25)", 'int', 1, 50
        )
        remaining_months_extra = self.get_user_input(
            "   Additional months (e.g., 6 for 6 extra months)", 'int', 0, 11, 0
        )
        
        remaining_months = (remaining_years * 12) + remaining_months_extra
        
        # Create mortgage object
        self.current_mortgage = MortgageDetails(
            rate=rate,
            balance=balance,
            payment=payment,
            remaining_months=remaining_months
        )
        
        # Display summary
        print(f"\n✅ CURRENT MORTGAGE SUMMARY:")
        print(f"   Rate: {rate*100:.3f}%")
        print(f"   Balance: ${balance:,.2f}")
        print(f"   Monthly Payment: ${payment:,.2f}")
        print(f"   Time Remaining: {remaining_years} years, {remaining_months_extra} months")
        
        return self.current_mortgage
    
    def get_refinance_scenarios(self) -> List[Tuple[str, RefinanceOptions]]:
        """Interactive input for refinance scenarios"""
        print("\n" + "="*60)
        print("📊 REFINANCE SCENARIOS TO COMPARE")
        print("="*60)
        print("Let's set up different refinance options to compare.")
        print("💡 Tip: Try different combinations of rates, terms, and points!")
        print()
        
        scenarios = []
        scenario_count = 1
        
        while True:
            print(f"\n🎯 SCENARIO {scenario_count}")
            print("-" * 30)
            
            # Scenario name
            scenario_name = self.get_user_input(
                f"📝 Scenario name (e.g., '30yr at 6.25%')",
                'str',
                default=f"Scenario {scenario_count}"
            )
            
            # New interest rate
            new_rate = self.get_user_input(
                "💰 New interest rate (e.g., 6.25 for 6.25%)",
                'float', 0.1, 20.0
            ) / 100
            
            # New loan term
            print("\n🕐 New loan term:")
            print("   Common options: 15 years (180 months), 20 years (240 months), 30 years (360 months)")
            new_term_years = self.get_user_input(
                "   Loan term in years (e.g., 30)", 'int', 5, 50
            )
            new_term_months = new_term_years * 12
            
            # Closing costs
            closing_costs = self.get_user_input(
                "💸 Total closing costs and fees (e.g., 8000 for $8,000)",
                'float', 0, 100000
            )
            
            # Buydown points
            use_points = self.get_user_input(
                "🎯 Do you want to buy down the rate with points? (y/n)",
                'bool'
            )
            
            buydown_points = 0.0
            rate_reduction_per_point = 0.0025  # Default 0.25% per point
            
            if use_points:
                buydown_points = self.get_user_input(
                    "   How many points? (e.g., 1.5 for 1.5 points)",
                    'float', 0, 5
                )
                
                rate_reduction_per_point = self.get_user_input(
                    "   Rate reduction per point (e.g., 0.25 for 0.25%)",
                    'float', 0.1, 1.0,
                    default=0.25
                ) / 100
            
            # Create refinance option
            refi_option = RefinanceOptions(
                new_rate=new_rate,
                new_term_months=new_term_months,
                closing_costs=closing_costs,
                buydown_points=buydown_points,
                rate_reduction_per_point=rate_reduction_per_point
            )
            
            scenarios.append((scenario_name, refi_option))
            
            # Show effective rate
            effective_rate = new_rate - (buydown_points * rate_reduction_per_point)
            print(f"\n✅ SCENARIO SUMMARY:")
            print(f"   Name: {scenario_name}")
            print(f"   Base Rate: {new_rate*100:.3f}%")
            if buydown_points > 0:
                print(f"   Points: {buydown_points}")
                print(f"   Effective Rate: {effective_rate*100:.3f}%")
            print(f"   Term: {new_term_years} years")
            print(f"   Closing Costs: ${closing_costs:,.2f}")
            
            # Ask for another scenario
            if scenario_count >= 5:
                print(f"\n⚠️  You've created {scenario_count} scenarios (maximum recommended)")
                add_another = False
            else:
                add_another = self.get_user_input(
                    f"\n➕ Add another scenario to compare? (y/n)",
                    'bool'
                )
            
            if not add_another:
                break
                
            scenario_count += 1
        
        self.scenarios = scenarios
        return scenarios
    
    def get_analysis_preferences(self) -> Dict:
        """Get user preferences for analysis"""
        print("\n" + "="*60)
        print("⚙️  ANALYSIS PREFERENCES")
        print("="*60)
        
        # Market data collection
        include_market_data = self.get_user_input(
            "🌐 Include real-time market data and expert forecasts? (y/n)\n" +
            "   (This will scrape current rates from financial websites)",
            'bool'
        )
        
        # Export preferences
        export_results = self.get_user_input(
            "📄 Export detailed results to CSV files? (y/n)",
            'bool'
        )
        
        return {
            'include_market_data': include_market_data,
            'export_results': export_results
        }
    
    def display_results(self, results_df: pd.DataFrame, preferences: Dict):
        """Display analysis results in a user-friendly format"""
        print("\n" + "="*80)
        print("🎯 REFINANCE ANALYSIS RESULTS")
        print("="*80)
        
        if preferences['include_market_data'] and hasattr(self.calculator, 'market_timing'):
            # Show market analysis first
            print(self.calculator.generate_market_report())
            print("\n" + "="*80)
        
        # Show scenario results
        print(f"\n📊 SCENARIO COMPARISON:")
        print("-" * 50)
        
        for i, (_, row) in enumerate(results_df.iterrows(), 1):
            print(f"\n{i}. 📋 {row['custom_scenario_name']}")
            print("   " + "-" * 40)
            
            # Basic metrics
            print(f"   💰 New Monthly Payment: ${row['new_monthly_payment']:,.2f}")
            print(f"   📉 Monthly Savings: ${row['monthly_savings']:,.2f}")
            print(f"   💸 Total Upfront Costs: ${row['total_upfront_cost']:,.2f}")
            
            # Rate information
            if row['buydown_points'] > 0:
                print(f"   🎯 Buydown Points: {row['buydown_points']} (${row['buydown_cost']:,.2f})")
                print(f"   📊 Effective Rate: {row['effective_rate_after_buydown']:.3f}%")
            else:
                print(f"   📊 Interest Rate: {row['effective_rate_after_buydown']:.3f}%")
            
            # Break-even analysis
            if isinstance(row['break_even_years'], (int, float)) and row['break_even_years'] != float('inf'):
                print(f"   ⚖️  Break-Even Time: {row['break_even_years']:.1f} years ({row['break_even_months']:.0f} months)")
            else:
                print(f"   ⚖️  Break-Even Time: Never")
            
            # Savings projections
            print(f"   💵 5-Year Net Savings: ${row['savings_5_years']:,.2f}")
            print(f"   💵 10-Year Net Savings: ${row['savings_10_years']:,.2f}")
            
            # Market comparison (if available)
            if 'rate_vs_market_30yr' in row and pd.notnull(row['rate_vs_market_30yr']):
                market_diff = row['rate_vs_market_30yr']
                if abs(market_diff) < 0.01:
                    market_note = "At current market rate"
                elif market_diff > 0:
                    market_note = f"{market_diff:.3f}% above market"
                else:
                    market_note = f"{abs(market_diff):.3f}% below market"
                print(f"   🌐 Market Comparison: {market_note}")
            
            # Recommendation
            if 'enhanced_recommendation' in row and pd.notnull(row['enhanced_recommendation']):
                print(f"   🏆 Recommendation: {row['enhanced_recommendation']}")
            else:
                print(f"   🏆 Recommendation: {row['recommendation']}")
        
        # Summary and best option
        print(f"\n" + "="*80)
        print("🏆 SUMMARY & RECOMMENDATIONS")
        print("="*80)
        
        # Find best scenarios
        best_monthly_savings = results_df.loc[results_df['monthly_savings'].idxmax()]
        best_5yr_savings = results_df.loc[results_df['savings_5_years'].idxmax()]
        
        print(f"\n💰 Best Monthly Savings: {best_monthly_savings['custom_scenario_name']}")
        print(f"   Saves ${best_monthly_savings['monthly_savings']:,.2f}/month")
        
        print(f"\n📈 Best 5-Year Value: {best_5yr_savings['custom_scenario_name']}")
        print(f"   Net 5-year savings: ${best_5yr_savings['savings_5_years']:,.2f}")
        
        # Quick break-even scenarios
        quick_breakeven = results_df[
            (results_df['break_even_years'].notna()) & 
            (results_df['break_even_years'] != float('inf')) & 
            (results_df['break_even_years'] <= 2)
        ]
        
        if not quick_breakeven.empty:
            print(f"\n⚡ Quick Break-Even Options (≤2 years):")
            for _, row in quick_breakeven.iterrows():
                print(f"   • {row['custom_scenario_name']}: {row['break_even_years']:.1f} years")
        
        # Market timing advice (if available)
        if preferences['include_market_data'] and hasattr(self.calculator, 'market_timing'):
            timing = self.calculator.market_timing
            print(f"\n🌐 Market Timing Advice:")
            print(f"   Current Environment: {timing.current_rate_environment.title()}")
            print(f"   Expert Consensus: {timing.forecast_consensus.replace('_', ' ').title()}")
            print(f"   Timing Recommendation: {timing.timing_recommendation.replace('_', ' ').title()}")
            print(f"   Confidence: {timing.confidence_score*100:.0f}%")
            print(f"   💡 {timing.reasoning}")
    
    def export_results(self, results_df: pd.DataFrame):
        """Export results and provide file information"""
        try:
            files = self.calculator.export_enhanced_analysis()
            print(f"\n✅ RESULTS EXPORTED:")
            for file in files:
                print(f"   📄 {file}")
            print(f"\n💡 Open these files in Excel for detailed analysis and sharing!")
        except Exception as e:
            print(f"\n❌ Error exporting results: {str(e)}")
    
    def run_interactive_session(self):
        """Run the complete interactive session"""
        print("🏠 ENHANCED MORTGAGE REFINANCE CALCULATOR")
        print("="*60)
        print("💡 This calculator helps you decide if refinancing makes sense")
        print("🌐 Includes real-time market data and expert forecasts")
        print("📊 Compares multiple scenarios with detailed break-even analysis")
        print()
        print("Let's get started! 🚀")
        
        try:
            # Step 1: Get current mortgage details
            self.get_current_mortgage_details()
            
            # Step 2: Get refinance scenarios
            self.get_refinance_scenarios()
            
            # Step 3: Get analysis preferences
            preferences = self.get_analysis_preferences()
            
            # Step 4: Run analysis
            print(f"\n🔄 Running analysis...")
            if preferences['include_market_data']:
                print("   🌐 Collecting market data (this may take 30-60 seconds)...")
            
            results_df = self.calculator.enhanced_refinance_analysis(
                self.current_mortgage,
                self.scenarios,
                include_market_rates=preferences['include_market_data']
            )
            
            # Step 5: Display results
            self.display_results(results_df, preferences)
            
            # Step 6: Export results if requested
            if preferences['export_results']:
                self.export_results(results_df)
            
            print(f"\n🎉 Analysis complete! Hope this helps with your decision! 🤝")
            
        except KeyboardInterrupt:
            print(f"\n👋 Analysis cancelled. Goodbye!")
        except Exception as e:
            print(f"\n❌ An error occurred: {str(e)}")
            print(f"💡 Try running the basic calculator if this continues to fail.")

def main():
    """Run the interactive mortgage calculator"""
    calculator = InteractiveMortgageCalculator()
    calculator.run_interactive_session()

if __name__ == "__main__":
    main()