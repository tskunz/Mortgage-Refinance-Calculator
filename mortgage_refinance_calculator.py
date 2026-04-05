#!/usr/bin/env python3
"""
Mortgage Refinance Calculator
Analyzes break-even points and total savings for mortgage refinancing decisions
"""

import numpy as np
import pandas as pd
from datetime import datetime
import csv
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

@dataclass
class MortgageDetails:
    """Container for mortgage details"""
    rate: float  # Annual interest rate (as decimal, e.g., 0.065 for 6.5%)
    balance: float  # Outstanding mortgage balance
    payment: float  # Current monthly payment (P&I only)
    remaining_months: int  # Remaining months on current loan
    extra_monthly_payment: float = 0.0
    extra_one_time_payment: float = 0.0

@dataclass
class RefinanceOptions:
    """Container for refinance options"""
    new_rate: float  # New annual interest rate (as decimal)
    new_term_months: int  # New loan term in months (typically 360 for 30-year)
    closing_costs: float  # Total closing costs and fees
    buydown_points: float = 0.0  # Number of points to buy down (e.g., 1.5 for 1.5 points)
    point_cost_per_point: float = 0.01  # Cost per point as % of loan amount (default 1%)
    rate_reduction_per_point: float = 0.0025  # Rate reduction per point (default 0.25%)
    extra_monthly_payment: float = 0.0
    extra_one_time_payment: float = 0.0

@dataclass
class RecastOptions:
    """Container for recast options"""
    lump_sum_payment: float  # Lump sum amount to apply towards principal
    recast_fee: float = 250.0  # Typical fee for recasting
    extra_monthly_payment: float = 0.0
    extra_one_time_payment: float = 0.0

class MortgageRefinanceCalculator:
    """Comprehensive mortgage refinance analysis calculator"""
    
    def __init__(self):
        self.results = []
    
    def calculate_monthly_payment(self, principal: float, annual_rate: float, months: int) -> float:
        """Calculate monthly payment using standard mortgage formula"""
        if annual_rate == 0:
            return principal / months
        
        monthly_rate = annual_rate / 12
        payment = principal * (monthly_rate * (1 + monthly_rate)**months) / ((1 + monthly_rate)**months - 1)
        return payment
    
    def generate_amortization_schedule(self, principal: float, annual_rate: float,
                                       base_monthly_payment: float,
                                       extra_monthly: float = 0.0,
                                       extra_one_time: float = 0.0,
                                       max_months: int = 3600) -> Dict:
        """Simulate month-by-month paydown, returning totals and the schedule array."""
        schedule = []
        balance = principal
        total_interest = 0.0
        months_elapsed = 0
        monthly_rate = annual_rate / 12 if annual_rate > 0 else 0
        
        while balance > 0 and months_elapsed < max_months:
            months_elapsed += 1
            current_extra = extra_monthly + (extra_one_time if months_elapsed == 1 else 0.0)
            
            interest_payment = balance * monthly_rate
            total_payment = base_monthly_payment + current_extra
            
            principal_payment = total_payment - interest_payment
            
            if principal_payment >= balance:
                principal_payment = balance
                total_payment = balance + interest_payment
                
            balance -= principal_payment
            total_interest += interest_payment
            
            if principal_payment <= 0 and current_extra <= 0:
                if months_elapsed > 1000:  # Prevent bad input loops
                    break
                    
            schedule.append({
                "month": months_elapsed,
                "balance": balance,
                "interest_paid": interest_payment,
                "principal_paid": principal_payment,
                "total_payment": total_payment
            })
            
        return {
            "schedule": schedule,
            "months_to_payoff": months_elapsed,
            "total_interest": total_interest,
            "total_payments": principal + total_interest
        }
    
    def analyze_refinance(self, current_mortgage: MortgageDetails, refi_options: RefinanceOptions) -> Dict:
        """Comprehensive refinance analysis"""
        
        # Current loan schedule calculation
        current_res = self.generate_amortization_schedule(
            principal=current_mortgage.balance, 
            annual_rate=current_mortgage.rate, 
            base_monthly_payment=current_mortgage.payment,
            extra_monthly=current_mortgage.extra_monthly_payment,
            extra_one_time=current_mortgage.extra_one_time_payment
        )
        current_total_interest = current_res["total_interest"]
        current_total_payments = current_res["total_payments"]
        current_months_to_payoff = current_res["months_to_payoff"]
        
        # Calculate refinance details
        effective_rate = refi_options.new_rate - (refi_options.buydown_points * refi_options.rate_reduction_per_point)
        buydown_cost = current_mortgage.balance * (refi_options.buydown_points * refi_options.point_cost_per_point)
        total_upfront_cost = refi_options.closing_costs + buydown_cost
        
        base_new_monthly_payment = self.calculate_monthly_payment(
            current_mortgage.balance, effective_rate, refi_options.new_term_months
        )
        
        new_res = self.generate_amortization_schedule(
            principal=current_mortgage.balance,
            annual_rate=effective_rate,
            base_monthly_payment=base_new_monthly_payment,
            extra_monthly=refi_options.extra_monthly_payment,
            extra_one_time=refi_options.extra_one_time_payment
        )
        new_total_interest = new_res["total_interest"]
        new_total_payments = new_res["total_payments"]
        new_months_to_payoff = new_res["months_to_payoff"]
        
        monthly_savings = current_mortgage.payment - base_new_monthly_payment
        
        # Break-even roughly based on base payment drop
        break_even_months = total_upfront_cost / monthly_savings if monthly_savings > 0 else float('inf')
        break_even_years = break_even_months / 12
        
        # Net savings arrays over 5/10/full term
        sched_curr = current_res['schedule']
        sched_new = new_res['schedule']
        
        def calculate_horizon_net(months_limit):
            curr_slice = sched_curr[:months_limit]
            new_slice = sched_new[:months_limit]
            curr_paid = sum(x['total_payment'] for x in curr_slice)
            new_paid = sum(x['total_payment'] for x in new_slice)
            
            curr_bal = curr_slice[-1]['balance'] if curr_slice else current_mortgage.balance
            new_bal = new_slice[-1]['balance'] if new_slice else current_mortgage.balance
            
            # (Cash outflows current + End debt current) vs (Cash outflows + End debt new)
            curr_net_cost = curr_paid + curr_bal
            new_net_cost = new_paid + new_bal + total_upfront_cost
            return curr_net_cost - new_net_cost
            
        savings_5_years = calculate_horizon_net(60)
        savings_10_years = calculate_horizon_net(120)
        savings_full_term = current_total_payments - (new_total_payments + total_upfront_cost)
        
        interest_savings_full_term = current_total_interest - new_total_interest
        net_interest_savings = interest_savings_full_term - total_upfront_cost
        
        return {
            'scenario_name': f"Refi: {effective_rate*100:.3f}% rate, {refi_options.new_term_months//12}yr term",
            'current_rate': current_mortgage.rate * 100,
            'current_payment': current_mortgage.payment,
            'current_remaining_balance': current_mortgage.balance,
            'current_remaining_months': current_months_to_payoff,
            'current_total_payments_remaining': current_total_payments,
            'current_total_interest_remaining': current_total_interest,
            
            'new_rate_before_buydown': refi_options.new_rate * 100,
            'buydown_points': refi_options.buydown_points,
            'buydown_cost': buydown_cost,
            'effective_rate_after_buydown': effective_rate * 100,
            'new_monthly_payment': base_new_monthly_payment,
            'new_term_months': refi_options.new_term_months,
            'new_payoff_months': new_months_to_payoff,
            'closing_costs': refi_options.closing_costs,
            'total_upfront_cost': total_upfront_cost,
            
            'monthly_savings': monthly_savings,
            'break_even_months': break_even_months if break_even_months != float('inf') else 'Never',
            'break_even_years': break_even_years if break_even_years != float('inf') else 'Never',
            
            'new_total_payments': new_total_payments,
            'new_total_interest': new_total_interest,
            
            'savings_5_years': savings_5_years,
            'savings_10_years': savings_10_years,
            'savings_full_term': savings_full_term,
            
            'interest_savings_full_term': interest_savings_full_term,
            'net_interest_savings': net_interest_savings,
            'schedule_current': current_res['schedule'],
            'schedule_new': new_res['schedule'],
            'recommendation': self._generate_recommendation(break_even_years, monthly_savings, savings_5_years)
        }
    
    def _generate_recommendation(self, break_even_years: float, monthly_savings: float, savings_5_years: float) -> str:
        """Generate recommendation based on analysis"""
        if monthly_savings <= 0:
            return "NOT RECOMMENDED - Higher monthly payment"
        elif break_even_years == float('inf'):
            return "NOT RECOMMENDED - Never breaks even"
        elif break_even_years <= 2:
            return "HIGHLY RECOMMENDED - Quick break-even"
        elif break_even_years <= 5 and savings_5_years > 0:
            return "RECOMMENDED - Reasonable break-even period"
        elif break_even_years <= 10:
            return "CONSIDER - Long break-even but potential savings"
        else:
            return "NOT RECOMMENDED - Break-even too long"
            
    def analyze_recast(self, current_mortgage: MortgageDetails, recast_options: RecastOptions) -> Dict:
        """Analyze the impact of a mortgage recast"""
        current_res = self.generate_amortization_schedule(
            principal=current_mortgage.balance, 
            annual_rate=current_mortgage.rate, 
            base_monthly_payment=current_mortgage.payment,
            extra_monthly=current_mortgage.extra_monthly_payment,
            extra_one_time=current_mortgage.extra_one_time_payment
        )
        current_total_interest = current_res["total_interest"]
        current_total_payments = current_res["total_payments"]
        current_months_to_payoff = current_res["months_to_payoff"]
        
        new_balance = max(0, current_mortgage.balance - recast_options.lump_sum_payment)
        
        if new_balance == 0:
            base_new_monthly_payment = 0
            new_res = {"schedule": [], "total_interest": 0, "total_payments": 0, "months_to_payoff": 0}
        else:
            base_new_monthly_payment = self.calculate_monthly_payment(
                new_balance, current_mortgage.rate, current_mortgage.remaining_months
            )
            new_res = self.generate_amortization_schedule(
                principal=new_balance,
                annual_rate=current_mortgage.rate,
                base_monthly_payment=base_new_monthly_payment,
                extra_monthly=recast_options.extra_monthly_payment,
                extra_one_time=recast_options.extra_one_time_payment
            )
            
        new_total_interest = new_res["total_interest"]
        new_total_payments = new_res["total_payments"]
        new_months_to_payoff = new_res["months_to_payoff"]
        
        monthly_savings = current_mortgage.payment - base_new_monthly_payment
        total_interest_savings = current_total_interest - new_total_interest
        net_savings_full_term = total_interest_savings - recast_options.recast_fee
        
        # Horizon savings
        sched_curr = current_res['schedule']
        sched_new = new_res['schedule']
        
        def calculate_horizon_net(months_limit):
            curr_slice = sched_curr[:months_limit]
            new_slice = sched_new[:months_limit]
            curr_paid = sum(x['total_payment'] for x in curr_slice)
            new_paid = sum(x['total_payment'] for x in new_slice)
            
            curr_bal = curr_slice[-1]['balance'] if curr_slice else current_mortgage.balance
            new_bal = new_slice[-1]['balance'] if new_slice else new_balance
            
            curr_net_cost = curr_paid + curr_bal
            new_net_cost = new_paid + new_bal + recast_options.lump_sum_payment + recast_options.recast_fee
            return curr_net_cost - new_net_cost
            
        savings_5_years = calculate_horizon_net(60)
        savings_10_years = calculate_horizon_net(120)

        # Create recommendation
        if recast_options.lump_sum_payment <= 0:
            rec = "NOT RECOMMENDED - No lump sum provided"
        elif monthly_savings < current_mortgage.payment * 0.05:
            rec = "CONSIDER - Low monthly impact; consider just making extra payments"
        else:
            rec = "RECOMMENDED - Significant monthly payment drop"

        return {
            'scenario_name': f"Recast: ${recast_options.lump_sum_payment:,.0f} lump sum",
            'current_rate': current_mortgage.rate * 100,
            'current_payment': current_mortgage.payment,
            'current_remaining_balance': current_mortgage.balance,
            'current_remaining_months': current_months_to_payoff,
            'current_total_payments_remaining': current_total_payments,
            'current_total_interest_remaining': current_total_interest,
            
            'lump_sum_payment': recast_options.lump_sum_payment,
            'recast_fee': recast_options.recast_fee,
            'new_balance': new_balance,
            'new_monthly_payment': base_new_monthly_payment,
            'new_payoff_months': new_months_to_payoff,
            
            'monthly_savings': monthly_savings,
            'new_total_payments': new_total_payments,
            'new_total_interest': new_total_interest,
            
            'interest_savings_full_term': total_interest_savings,
            'net_interest_savings': net_savings_full_term,
            'savings_5_years': savings_5_years,
            'savings_10_years': savings_10_years,
            'savings_full_term': calculate_horizon_net(max(current_months_to_payoff, new_months_to_payoff)),
            
            'recommendation': rec,
            
            'schedule_current': current_res['schedule'],
            'schedule_new': new_res['schedule'],
            
            # Additional placeholders
            'new_rate_before_buydown': current_mortgage.rate * 100,
            'effective_rate_after_buydown': current_mortgage.rate * 100,
            'buydown_points': 0,
            'buydown_cost': 0,
            'closing_costs': recast_options.recast_fee,
            'total_upfront_cost': recast_options.recast_fee,
            'break_even_months': 'Immediate',
            'break_even_years': 'Immediate',
            'new_term_months': current_mortgage.remaining_months
        }
    
    def compare_scenarios(self, current_mortgage: MortgageDetails, 
                         scenarios: List[Tuple[str, RefinanceOptions]]) -> pd.DataFrame:
        """Compare multiple refinance scenarios"""
        results = []
        
        for scenario_name, refi_options in scenarios:
            analysis = self.analyze_refinance(current_mortgage, refi_options)
            analysis['custom_scenario_name'] = scenario_name
            results.append(analysis)
        
        self.results = results
        return pd.DataFrame(results)
    
    def export_to_csv(self, filename: str = None) -> str:
        """Export analysis results to CSV file"""
        if not self.results:
            raise ValueError("No analysis results to export. Run compare_scenarios first.")
        
        if filename is None:
            filename = f"mortgage_refi_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        df = pd.DataFrame(self.results)
        
        # Reorder columns for better readability
        column_order = [
            'custom_scenario_name', 'recommendation',
            'current_rate', 'new_rate_before_buydown', 'effective_rate_after_buydown',
            'buydown_points', 'buydown_cost', 'closing_costs', 'total_upfront_cost',
            'current_payment', 'new_monthly_payment', 'monthly_savings',
            'break_even_months', 'break_even_years',
            'savings_5_years', 'savings_10_years', 'savings_full_term',
            'current_remaining_balance', 'current_remaining_months', 'new_term_months',
            'current_total_payments_remaining', 'new_total_payments',
            'current_total_interest_remaining', 'new_total_interest',
            'interest_savings_full_term', 'net_interest_savings'
        ]
        
        # Only include columns that exist in the dataframe
        available_columns = [col for col in column_order if col in df.columns]
        df_ordered = df[available_columns]
        
        # Format currency columns
        currency_cols = [
            'current_payment', 'new_monthly_payment', 'monthly_savings',
            'buydown_cost', 'closing_costs', 'total_upfront_cost',
            'savings_5_years', 'savings_10_years', 'savings_full_term',
            'current_remaining_balance', 'current_total_payments_remaining', 'new_total_payments',
            'current_total_interest_remaining', 'new_total_interest',
            'interest_savings_full_term', 'net_interest_savings'
        ]
        
        for col in currency_cols:
            if col in df_ordered.columns:
                df_ordered[col] = df_ordered[col].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) and x != 'Never' else x)
        
        # Format percentage columns
        percentage_cols = ['current_rate', 'new_rate_before_buydown', 'effective_rate_after_buydown']
        for col in percentage_cols:
            if col in df_ordered.columns:
                df_ordered[col] = df_ordered[col].apply(lambda x: f"{x:.3f}%" if pd.notnull(x) else x)
        
        df_ordered.to_csv(filename, index=False)
        return filename

def main():
    """Example usage of the mortgage refinance calculator"""
    
    # Example current mortgage details
    current_mortgage = MortgageDetails(
        rate=0.0675,  # 6.75% current rate
        balance=450000,  # $450,000 remaining balance
        payment=3200,  # $3,200 current monthly payment
        remaining_months=300  # 25 years remaining
    )
    
    print("🏠 MORTGAGE REFINANCE CALCULATOR")
    print("=" * 50)
    print(f"Current Mortgage Details:")
    print(f"  Rate: {current_mortgage.rate*100:.3f}%")
    print(f"  Balance: ${current_mortgage.balance:,.2f}")
    print(f"  Monthly Payment: ${current_mortgage.payment:,.2f}")
    print(f"  Remaining Term: {current_mortgage.remaining_months//12} years {current_mortgage.remaining_months%12} months")
    print()
    
    # Define refinance scenarios to compare
    scenarios = [
        ("30yr @ 6.25% (No Points)", RefinanceOptions(
            new_rate=0.0625,
            new_term_months=360,
            closing_costs=8000
        )),
        ("30yr @ 6.00% (1 Point)", RefinanceOptions(
            new_rate=0.0625,
            new_term_months=360,
            closing_costs=8000,
            buydown_points=1.0,
            rate_reduction_per_point=0.0025
        )),
        ("30yr @ 5.75% (2 Points)", RefinanceOptions(
            new_rate=0.0625,
            new_term_months=360,
            closing_costs=8000,
            buydown_points=2.0,
            rate_reduction_per_point=0.0025
        )),
        ("15yr @ 5.75%", RefinanceOptions(
            new_rate=0.0575,
            new_term_months=180,
            closing_costs=8000
        )),
        ("20yr @ 6.00%", RefinanceOptions(
            new_rate=0.06,
            new_term_months=240,
            closing_costs=8000
        ))
    ]
    
    # Create calculator and run analysis
    calculator = MortgageRefinanceCalculator()
    results_df = calculator.compare_scenarios(current_mortgage, scenarios)
    
    # Display summary results
    print("REFINANCE SCENARIO COMPARISON")
    print("=" * 50)
    
    for _, row in results_df.iterrows():
        print(f"\n📊 {row['custom_scenario_name']}")
        print(f"   Effective Rate: {row['effective_rate_after_buydown']:.3f}%")
        print(f"   Monthly Payment: ${row['new_monthly_payment']:,.2f}")
        print(f"   Monthly Savings: ${row['monthly_savings']:,.2f}")
        print(f"   Break-even: {row['break_even_years']:.1f} years" if isinstance(row['break_even_years'], (int, float)) and row['break_even_years'] != float('inf') else f"   Break-even: {row['break_even_years']}")
        print(f"   5-Year Savings: ${row['savings_5_years']:,.2f}")
        print(f"   Recommendation: {row['recommendation']}")
    
    # Export to CSV
    filename = calculator.export_to_csv()
    print(f"\n✅ Analysis exported to: {filename}")
    
    return calculator, results_df

if __name__ == "__main__":
    calculator, results = main()