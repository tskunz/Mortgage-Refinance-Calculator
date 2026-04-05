#!/usr/bin/env python3
"""
Interactive Mortgage Refinance Calculator
Customize this with your actual mortgage details
"""

from mortgage_refinance_calculator import MortgageRefinanceCalculator, MortgageDetails, RefinanceOptions

def calculate_your_mortgage():
    """Customize these values with your actual mortgage details"""
    
    # 🏠 ENTER YOUR CURRENT MORTGAGE DETAILS HERE
    current_mortgage = MortgageDetails(
        rate=0.0675,  # Current interest rate (6.75% = 0.0675)
        balance=450000,  # Outstanding mortgage balance
        payment=3200,  # Current monthly payment (P&I only, no taxes/insurance)
        remaining_months=300  # Remaining months on current loan
    )
    
    # 📊 DEFINE YOUR REFINANCE SCENARIOS TO COMPARE
    scenarios = [
        # Scenario 1: Standard 30-year refi with no points
        ("30yr @ 6.25% (No Points)", RefinanceOptions(
            new_rate=0.0625,  # 6.25%
            new_term_months=360,  # 30 years
            closing_costs=8000  # Total closing costs
        )),
        
        # Scenario 2: Buy down rate with 1 point
        ("30yr @ 6.00% (1 Point)", RefinanceOptions(
            new_rate=0.0625,  # Base rate before buydown
            new_term_months=360,
            closing_costs=8000,
            buydown_points=1.0,  # Buy 1 point
            rate_reduction_per_point=0.0025  # 0.25% reduction per point
        )),
        
        # Scenario 3: Buy down rate with 2 points
        ("30yr @ 5.75% (2 Points)", RefinanceOptions(
            new_rate=0.0625,
            new_term_months=360,
            closing_costs=8000,
            buydown_points=2.0,  # Buy 2 points
            rate_reduction_per_point=0.0025
        )),
        
        # Scenario 4: 15-year mortgage for faster payoff
        ("15yr @ 5.75%", RefinanceOptions(
            new_rate=0.0575,  # 5.75%
            new_term_months=180,  # 15 years
            closing_costs=8000
        )),
        
        # Scenario 5: 20-year compromise
        ("20yr @ 6.00%", RefinanceOptions(
            new_rate=0.06,  # 6.00%
            new_term_months=240,  # 20 years
            closing_costs=8000
        ))
    ]
    
    print("🏠 YOUR MORTGAGE REFINANCE ANALYSIS")
    print("=" * 60)
    print(f"Current Mortgage:")
    print(f"  Rate: {current_mortgage.rate*100:.3f}%")
    print(f"  Balance: ${current_mortgage.balance:,.2f}")
    print(f"  Monthly Payment: ${current_mortgage.payment:,.2f}")
    print(f"  Remaining: {current_mortgage.remaining_months//12} years {current_mortgage.remaining_months%12} months")
    print("\n" + "=" * 60)
    
    # Run the analysis
    calculator = MortgageRefinanceCalculator()
    results_df = calculator.compare_scenarios(current_mortgage, scenarios)
    
    # Show detailed results
    for i, (_, row) in enumerate(results_df.iterrows(), 1):
        print(f"\n📊 SCENARIO {i}: {row['custom_scenario_name']}")
        print("-" * 40)
        print(f"   💰 New Monthly Payment: ${row['new_monthly_payment']:,.2f}")
        print(f"   📉 Monthly Savings: ${row['monthly_savings']:,.2f}")
        print(f"   💸 Upfront Costs: ${row['total_upfront_cost']:,.2f}")
        if row['buydown_points'] > 0:
            print(f"   🎯 Buydown Points: {row['buydown_points']} (costs ${row['buydown_cost']:,.2f})")
            print(f"   📊 Effective Rate: {row['effective_rate_after_buydown']:.3f}%")
        else:
            print(f"   📊 Interest Rate: {row['effective_rate_after_buydown']:.3f}%")
        
        if isinstance(row['break_even_years'], (int, float)) and row['break_even_years'] != float('inf'):
            print(f"   ⚖️  Break-Even: {row['break_even_years']:.1f} years ({row['break_even_months']:.0f} months)")
        else:
            print(f"   ⚖️  Break-Even: Never")
        
        print(f"   💵 5-Year Net Savings: ${row['savings_5_years']:,.2f}")
        print(f"   💵 10-Year Net Savings: ${row['savings_10_years']:,.2f}")
        print(f"   🏆 Recommendation: {row['recommendation']}")
    
    # Export results
    filename = calculator.export_to_csv()
    print(f"\n✅ Detailed analysis exported to: {filename}")
    print(f"📄 Open this CSV file in Excel for detailed comparison")
    
    # Summary recommendation
    print(f"\n🎯 QUICK SUMMARY:")
    print("=" * 60)
    best_scenario = results_df.loc[results_df['savings_5_years'].idxmax()]
    print(f"Best 5-year savings: {best_scenario['custom_scenario_name']}")
    print(f"Saves ${best_scenario['monthly_savings']:.2f}/month, breaks even in {best_scenario['break_even_years']:.1f} years")
    
    recommended = results_df[results_df['recommendation'].str.contains('RECOMMENDED', na=False)]
    if not recommended.empty:
        print(f"\nTop recommendation: {recommended.iloc[0]['custom_scenario_name']}")
        print(f"Reasoning: {recommended.iloc[0]['recommendation']}")
    
    return calculator, results_df

if __name__ == "__main__":
    calculator, results = calculate_your_mortgage()