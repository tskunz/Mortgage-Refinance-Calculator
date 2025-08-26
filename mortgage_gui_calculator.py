#!/usr/bin/env python3
"""
GUI Mortgage Refinance Calculator
User-friendly graphical interface with market data integration
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
from datetime import datetime, date
import threading
import os

# Try to import tkcalendar, fallback to text entry if not available
try:
    from tkcalendar import DateEntry
    HAS_CALENDAR = True
except ImportError:
    HAS_CALENDAR = False

# Import our enhanced calculator
from mortgage_enhanced_calculator import EnhancedMortgageCalculator
from mortgage_refinance_calculator import MortgageDetails, RefinanceOptions

class MortgageGUI:
    """GUI interface for mortgage refinance calculator"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Enhanced Mortgage Refinance Calculator")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # Calculator instance
        self.calculator = EnhancedMortgageCalculator()
        self.results_df = None
        
        # Variables for form inputs
        self.current_rate = tk.DoubleVar(value=6.75)
        self.current_balance = tk.DoubleVar(value=450000)
        self.current_payment = tk.DoubleVar(value=3200)
        # Default to 25 years from today
        default_maturity = datetime.now().date().replace(year=datetime.now().year + 25)
        self.maturity_date = tk.StringVar(value=default_maturity.strftime("%Y-%m-%d"))
        
        self.include_market_data = tk.BooleanVar(value=True)
        self.export_results = tk.BooleanVar(value=True)
        
        # Scenario variables (for up to 5 scenarios)
        self.scenario_vars = []
        for i in range(5):
            scenario = {
                'enabled': tk.BooleanVar(value=True if i < 3 else False),
                'name': tk.StringVar(value=f"Scenario {i+1}"),
                'rate': tk.DoubleVar(value=6.25 - (i * 0.25)),
                'term_years': tk.IntVar(value=30 if i != 2 else 15),
                'closing_costs': tk.DoubleVar(value=8000),
                'use_points': tk.BooleanVar(value=i == 1),
                'points': tk.DoubleVar(value=1.0),
                'point_reduction': tk.DoubleVar(value=0.25)
            }
            self.scenario_vars.append(scenario)
        
        self.create_widgets()
        
    def on_date_change(self, event=None):
        """Update maturity date string variable when date picker changes"""
        if HAS_CALENDAR and hasattr(self, 'maturity_date_picker'):
            self.maturity_date.set(self.maturity_date_picker.get_date().strftime("%Y-%m-%d"))
    
    def get_remaining_months(self):
        """Calculate remaining months from maturity date"""
        try:
            maturity = datetime.strptime(self.maturity_date.get(), "%Y-%m-%d").date()
            today = datetime.now().date()
            
            if maturity <= today:
                return 0
            
            # Calculate difference in months
            months = (maturity.year - today.year) * 12 + (maturity.month - today.month)
            
            # Adjust for day of month
            if maturity.day < today.day:
                months -= 1
            
            return max(0, months)
        except:
            return 300  # Default to 25 years if date parsing fails
        
    def create_widgets(self):
        """Create and layout all GUI widgets"""
        
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Tab 1: Current Mortgage
        current_frame = ttk.Frame(notebook)
        notebook.add(current_frame, text="Current Mortgage")
        self.create_current_mortgage_tab(current_frame)
        
        # Tab 2: Refinance Scenarios
        scenarios_frame = ttk.Frame(notebook)
        notebook.add(scenarios_frame, text="Refinance Scenarios")
        self.create_scenarios_tab(scenarios_frame)
        
        # Tab 3: Analysis Options
        options_frame = ttk.Frame(notebook)
        notebook.add(options_frame, text="Analysis Options")
        self.create_options_tab(options_frame)
        
        # Tab 4: Results
        results_frame = ttk.Frame(notebook)
        notebook.add(results_frame, text="Results")
        self.create_results_tab(results_frame)
        
        # Bottom frame for main buttons
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        ttk.Button(button_frame, text="🔄 Run Analysis", 
                  command=self.run_analysis, style='Accent.TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text="📄 Export Results", 
                  command=self.export_results).pack(side='left', padx=5)
        ttk.Button(button_frame, text="📊 Export Amortization", 
                  command=self.export_amortization_schedule).pack(side='left', padx=5)
        ttk.Button(button_frame, text="❓ Help", 
                  command=self.show_help).pack(side='right', padx=5)
    
    def create_current_mortgage_tab(self, parent):
        """Create current mortgage input tab"""
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        ttk.Label(main_frame, text="🏠 Current Mortgage Details", 
                 font=('Arial', 14, 'bold')).pack(anchor='w', pady=(0, 15))
        
        # Create form fields
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill='x')
        
        # Interest Rate
        rate_frame = ttk.Frame(form_frame)
        rate_frame.pack(fill='x', pady=5)
        ttk.Label(rate_frame, text="💰 Current Interest Rate (%):").pack(side='left', anchor='w')
        rate_entry = ttk.Entry(rate_frame, textvariable=self.current_rate, width=15)
        rate_entry.pack(side='right')
        
        # Balance
        balance_frame = ttk.Frame(form_frame)
        balance_frame.pack(fill='x', pady=5)
        ttk.Label(balance_frame, text="💵 Outstanding Balance ($):").pack(side='left', anchor='w')
        balance_entry = ttk.Entry(balance_frame, textvariable=self.current_balance, width=15)
        balance_entry.pack(side='right')
        
        # Payment
        payment_frame = ttk.Frame(form_frame)
        payment_frame.pack(fill='x', pady=5)
        ttk.Label(payment_frame, text="📅 Monthly Payment - P&I only ($):").pack(side='left', anchor='w')
        payment_entry = ttk.Entry(payment_frame, textvariable=self.current_payment, width=15)
        payment_entry.pack(side='right')
        
        # Maturity Date
        maturity_frame = ttk.Frame(form_frame)
        maturity_frame.pack(fill='x', pady=5)
        ttk.Label(maturity_frame, text="📅 Loan Maturity Date:").pack(side='left', anchor='w')
        
        # Date input - use calendar widget if available, otherwise text entry
        if HAS_CALENDAR:
            try:
                default_date = datetime.strptime(self.maturity_date.get(), "%Y-%m-%d").date()
            except:
                default_date = datetime.now().date().replace(year=datetime.now().year + 25)
            
            self.maturity_date_picker = DateEntry(maturity_frame, 
                                                width=12, 
                                                background='darkblue',
                                                foreground='white', 
                                                borderwidth=2,
                                                date_pattern='yyyy-mm-dd',
                                                year=default_date.year,
                                                month=default_date.month,
                                                day=default_date.day)
            self.maturity_date_picker.pack(side='right')
            
            # Update string variable when date changes
            self.maturity_date_picker.bind("<<DateEntrySelected>>", self.on_date_change)
        else:
            # Fallback to text entry
            date_entry = ttk.Entry(maturity_frame, textvariable=self.maturity_date, width=15)
            date_entry.pack(side='right')
            ttk.Label(maturity_frame, text="(YYYY-MM-DD)", foreground='gray').pack(side='right', padx=(0, 5))
    
    def create_scenarios_tab(self, parent):
        """Create refinance scenarios input tab"""
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        ttk.Label(main_frame, text="📊 Refinance Scenarios to Compare", 
                 font=('Arial', 14, 'bold')).pack(anchor='w', pady=(0, 15))
        
        # Scrollable frame for scenarios
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Create scenario input forms
        for i, scenario_vars in enumerate(self.scenario_vars):
            self.create_scenario_form(scrollable_frame, i, scenario_vars)
    
    def create_scenario_form(self, parent, index, scenario_vars):
        """Create individual scenario input form"""
        # Main scenario frame
        scenario_frame = ttk.LabelFrame(parent, text=f"Scenario {index + 1}")
        scenario_frame.pack(fill='x', pady=10, padx=5)
        
        # Enable checkbox
        ttk.Checkbutton(scenario_frame, text="Include this scenario", 
                       variable=scenario_vars['enabled']).pack(anchor='w', pady=5)
        
        # Form fields in a grid
        form_frame = ttk.Frame(scenario_frame)
        form_frame.pack(fill='x', padx=10, pady=5)
        
        # Row 1: Name and Rate
        ttk.Label(form_frame, text="Name:").grid(row=0, column=0, sticky='w', padx=(0, 5))
        ttk.Entry(form_frame, textvariable=scenario_vars['name'], width=20).grid(row=0, column=1, padx=5)
        
        ttk.Label(form_frame, text="Rate (%):").grid(row=0, column=2, sticky='w', padx=(10, 5))
        ttk.Entry(form_frame, textvariable=scenario_vars['rate'], width=10).grid(row=0, column=3, padx=5)
        
        # Row 2: Term and Closing Costs
        ttk.Label(form_frame, text="Term (years):").grid(row=1, column=0, sticky='w', padx=(0, 5), pady=5)
        ttk.Entry(form_frame, textvariable=scenario_vars['term_years'], width=10).grid(row=1, column=1, padx=5)
        
        ttk.Label(form_frame, text="Closing Costs ($):").grid(row=1, column=2, sticky='w', padx=(10, 5))
        ttk.Entry(form_frame, textvariable=scenario_vars['closing_costs'], width=10).grid(row=1, column=3, padx=5)
        
        # Row 3: Points
        points_frame = ttk.Frame(form_frame)
        points_frame.grid(row=2, column=0, columnspan=4, sticky='w', pady=5)
        
        ttk.Checkbutton(points_frame, text="Buy down with points:", 
                       variable=scenario_vars['use_points']).pack(side='left')
        ttk.Entry(points_frame, textvariable=scenario_vars['points'], width=8).pack(side='left', padx=5)
        ttk.Label(points_frame, text="points @").pack(side='left')
        ttk.Entry(points_frame, textvariable=scenario_vars['point_reduction'], width=8).pack(side='left', padx=5)
        ttk.Label(points_frame, text="% reduction").pack(side='left')
    
    def create_options_tab(self, parent):
        """Create analysis options tab"""
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        ttk.Label(main_frame, text="⚙️ Analysis Options", 
                 font=('Arial', 14, 'bold')).pack(anchor='w', pady=(0, 15))
        
        # Market data option
        market_frame = ttk.LabelFrame(main_frame, text="Market Data")
        market_frame.pack(fill='x', pady=10)
        
        ttk.Checkbutton(market_frame, text="🌐 Include real-time market data and expert forecasts", 
                       variable=self.include_market_data).pack(anchor='w', padx=10, pady=10)
        
        ttk.Label(market_frame, text="This will scrape current rates from financial websites\n" +
                                   "and provide market timing recommendations.\n" +
                                   "(May take 30-60 seconds)", 
                 foreground='gray').pack(anchor='w', padx=20, pady=(0, 10))
        
        # Export option
        export_frame = ttk.LabelFrame(main_frame, text="Export Results")
        export_frame.pack(fill='x', pady=10)
        
        ttk.Checkbutton(export_frame, text="📄 Automatically export results to CSV files", 
                       variable=self.export_results).pack(anchor='w', padx=10, pady=10)
    
    def create_results_tab(self, parent):
        """Create results display tab"""
        self.results_frame = ttk.Frame(parent)
        self.results_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Results will be populated when analysis runs
        self.results_text = tk.Text(self.results_frame, wrap=tk.WORD, font=('Consolas', 10))
        results_scrollbar = ttk.Scrollbar(self.results_frame, orient="vertical", command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=results_scrollbar.set)
        
        self.results_text.pack(side="left", fill="both", expand=True)
        results_scrollbar.pack(side="right", fill="y")
        
        # Initial message
        self.results_text.insert(tk.END, "📊 Results will appear here after running the analysis...\n\n")
        self.results_text.insert(tk.END, "💡 Click 'Run Analysis' to get started!")
        self.results_text.config(state=tk.DISABLED)
    
    def run_analysis(self):
        """Run the mortgage refinance analysis"""
        try:
            # Validate inputs
            if not self.validate_inputs():
                return
            
            # Update UI to show analysis is running
            self.results_text.config(state=tk.NORMAL)
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, "🔄 Running analysis...\n\n")
            if self.include_market_data.get():
                self.results_text.insert(tk.END, "🌐 Collecting market data (this may take 30-60 seconds)...\n")
            self.results_text.config(state=tk.DISABLED)
            self.root.update()
            
            # Run analysis in a thread to prevent GUI freezing
            def analysis_thread():
                try:
                    # Create mortgage details
                    current_mortgage = MortgageDetails(
                        rate=self.current_rate.get() / 100,
                        balance=self.current_balance.get(),
                        payment=self.current_payment.get(),
                        remaining_months=self.get_remaining_months()
                    )
                    
                    # Create scenarios
                    scenarios = []
                    for i, scenario_vars in enumerate(self.scenario_vars):
                        if scenario_vars['enabled'].get():
                            buydown_points = scenario_vars['points'].get() if scenario_vars['use_points'].get() else 0.0
                            rate_reduction = scenario_vars['point_reduction'].get() / 100 if scenario_vars['use_points'].get() else 0.0025
                            
                            refi_option = RefinanceOptions(
                                new_rate=scenario_vars['rate'].get() / 100,
                                new_term_months=scenario_vars['term_years'].get() * 12,
                                closing_costs=scenario_vars['closing_costs'].get(),
                                buydown_points=buydown_points,
                                rate_reduction_per_point=rate_reduction
                            )
                            
                            scenarios.append((scenario_vars['name'].get(), refi_option))
                    
                    # Run enhanced analysis
                    self.results_df = self.calculator.enhanced_refinance_analysis(
                        current_mortgage, 
                        scenarios, 
                        include_market_rates=self.include_market_data.get()
                    )
                    
                    # Update UI with results
                    self.root.after(0, self.display_results)
                    
                except Exception as e:
                    self.root.after(0, lambda: self.show_error(f"Analysis error: {str(e)}"))
            
            # Start analysis thread
            thread = threading.Thread(target=analysis_thread)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            self.show_error(f"Error starting analysis: {str(e)}")
    
    def display_results(self):
        """Display analysis results in the results tab"""
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)
        
        # Market analysis (if available)
        if hasattr(self.calculator, 'market_timing') and self.calculator.market_timing:
            market_report = self.calculator.generate_market_report()
            self.results_text.insert(tk.END, market_report + "\n\n")
            self.results_text.insert(tk.END, "="*80 + "\n\n")
        
        # Scenario results
        self.results_text.insert(tk.END, "📊 REFINANCE SCENARIO RESULTS\n")
        self.results_text.insert(tk.END, "="*50 + "\n\n")
        
        for i, (_, row) in enumerate(self.results_df.iterrows(), 1):
            self.results_text.insert(tk.END, f"{i}. 📋 {row['custom_scenario_name']}\n")
            self.results_text.insert(tk.END, "   " + "-"*40 + "\n")
            self.results_text.insert(tk.END, f"   💰 New Monthly Payment: ${row['new_monthly_payment']:,.2f}\n")
            self.results_text.insert(tk.END, f"   📉 Monthly Savings: ${row['monthly_savings']:,.2f}\n")
            self.results_text.insert(tk.END, f"   💸 Total Upfront Costs: ${row['total_upfront_cost']:,.2f}\n")
            
            if row['buydown_points'] > 0:
                self.results_text.insert(tk.END, f"   🎯 Buydown Points: {row['buydown_points']} (${row['buydown_cost']:,.2f})\n")
                self.results_text.insert(tk.END, f"   📊 Effective Rate: {row['effective_rate_after_buydown']:.3f}%\n")
            else:
                self.results_text.insert(tk.END, f"   📊 Interest Rate: {row['effective_rate_after_buydown']:.3f}%\n")
            
            if isinstance(row['break_even_years'], (int, float)) and row['break_even_years'] != float('inf'):
                self.results_text.insert(tk.END, f"   ⚖️  Break-Even Time: {row['break_even_years']:.1f} years\n")
            else:
                self.results_text.insert(tk.END, f"   ⚖️  Break-Even Time: Never\n")
            
            self.results_text.insert(tk.END, f"   💵 5-Year Net Savings: ${row['savings_5_years']:,.2f}\n")
            
            if 'enhanced_recommendation' in row and pd.notnull(row['enhanced_recommendation']):
                self.results_text.insert(tk.END, f"   🏆 Recommendation: {row['enhanced_recommendation']}\n")
            else:
                self.results_text.insert(tk.END, f"   🏆 Recommendation: {row['recommendation']}\n")
            
            self.results_text.insert(tk.END, "\n")
        
        # Summary
        best_5yr = self.results_df.loc[self.results_df['savings_5_years'].idxmax()]
        self.results_text.insert(tk.END, f"🏆 BEST 5-YEAR VALUE: {best_5yr['custom_scenario_name']}\n")
        self.results_text.insert(tk.END, f"   Net 5-year savings: ${best_5yr['savings_5_years']:,.2f}\n\n")
        
        self.results_text.insert(tk.END, "✅ Analysis complete!\n")
        if self.export_results.get():
            self.results_text.insert(tk.END, "📄 Results exported to CSV files.\n")
        
        self.results_text.config(state=tk.DISABLED)
        
        # Auto-export if enabled
        if self.export_results.get():
            self.export_results_files()
    
    def validate_inputs(self):
        """Validate user inputs"""
        try:
            # Check required fields
            if self.current_rate.get() <= 0 or self.current_rate.get() > 20:
                messagebox.showerror("Invalid Input", "Current interest rate must be between 0.1% and 20%")
                return False
            
            if self.current_balance.get() <= 0:
                messagebox.showerror("Invalid Input", "Outstanding balance must be greater than $0")
                return False
            
            if self.current_payment.get() <= 0:
                messagebox.showerror("Invalid Input", "Monthly payment must be greater than $0")
                return False
            
            if self.get_remaining_months() <= 0:
                messagebox.showerror("Invalid Input", "Maturity date must be in the future")
                return False
            
            # Check that at least one scenario is enabled
            enabled_scenarios = sum(1 for sv in self.scenario_vars if sv['enabled'].get())
            if enabled_scenarios == 0:
                messagebox.showerror("Invalid Input", "Please enable at least one refinance scenario")
                return False
            
            return True
            
        except Exception as e:
            messagebox.showerror("Validation Error", f"Error validating inputs: {str(e)}")
            return False
    
    def export_results_files(self):
        """Export results to files"""
        try:
            files = self.calculator.export_enhanced_analysis()
            message = "Results exported to:\n" + "\n".join(files)
            messagebox.showinfo("Export Complete", message)
        except Exception as e:
            messagebox.showerror("Export Error", f"Error exporting results: {str(e)}")
    
    def export_results(self):
        """Manual export results"""
        if self.results_df is None:
            messagebox.showwarning("No Results", "Please run the analysis first")
            return
        
        self.export_results_files()
    
    def export_amortization_schedule(self):
        """Export amortization schedule to CSV"""
        try:
            # Validate current mortgage inputs
            if not self.validate_current_mortgage_inputs():
                return
            
            # Ask user which scenario to use for amortization
            scenario_choice = self.get_scenario_choice()
            if scenario_choice is None:
                return
            
            # Generate amortization schedule
            if scenario_choice == "current":
                schedule_df = self.generate_current_mortgage_schedule()
                filename_prefix = "current_mortgage"
            else:
                schedule_df = self.generate_scenario_schedule(scenario_choice)
                scenario_name = self.scenario_vars[scenario_choice]['name'].get().replace(" ", "_").lower()
                filename_prefix = f"scenario_{scenario_name}"
            
            # Save to CSV with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{filename_prefix}_amortization_{timestamp}.csv"
            
            schedule_df.to_csv(filename, index=False)
            
            messagebox.showinfo("Export Complete", 
                              f"Amortization schedule exported to:\n{filename}")
                              
        except Exception as e:
            messagebox.showerror("Export Error", f"Error exporting amortization schedule: {str(e)}")
    
    def validate_current_mortgage_inputs(self):
        """Validate current mortgage inputs for amortization"""
        try:
            if self.current_rate.get() <= 0 or self.current_rate.get() > 20:
                messagebox.showerror("Invalid Input", "Current interest rate must be between 0.1% and 20%")
                return False
            
            if self.current_balance.get() <= 0:
                messagebox.showerror("Invalid Input", "Outstanding balance must be greater than $0")
                return False
            
            if self.get_remaining_months() <= 0:
                messagebox.showerror("Invalid Input", "Maturity date must be in the future")
                return False
            
            return True
            
        except Exception as e:
            messagebox.showerror("Validation Error", f"Error validating inputs: {str(e)}")
            return False
    
    def get_scenario_choice(self):
        """Let user choose which scenario to export amortization for"""
        choice_window = tk.Toplevel(self.root)
        choice_window.title("Choose Scenario")
        choice_window.geometry("400x300")
        choice_window.transient(self.root)
        choice_window.grab_set()
        
        result = [None]
        
        ttk.Label(choice_window, text="Select scenario for amortization schedule:", 
                 font=('Arial', 12, 'bold')).pack(pady=10)
        
        # Current mortgage option
        ttk.Button(choice_window, text="🏠 Current Mortgage", 
                  command=lambda: self.set_choice(result, choice_window, "current")).pack(pady=5, fill='x', padx=20)
        
        # Scenario options
        for i, scenario_vars in enumerate(self.scenario_vars):
            if scenario_vars['enabled'].get():
                scenario_name = scenario_vars['name'].get()
                rate = scenario_vars['rate'].get()
                term = scenario_vars['term_years'].get()
                
                button_text = f"📊 {scenario_name} ({rate}%, {term}yr)"
                ttk.Button(choice_window, text=button_text,
                          command=lambda idx=i: self.set_choice(result, choice_window, idx)).pack(pady=2, fill='x', padx=20)
        
        ttk.Button(choice_window, text="Cancel", 
                  command=lambda: self.set_choice(result, choice_window, None)).pack(pady=10)
        
        choice_window.wait_window()
        return result[0]
    
    def set_choice(self, result, window, choice):
        """Helper method to set choice and close window"""
        result[0] = choice
        window.destroy()
    
    def generate_current_mortgage_schedule(self):
        """Generate amortization schedule for current mortgage"""
        balance = self.current_balance.get()
        rate = self.current_rate.get() / 100 / 12  # Monthly rate
        remaining_months = self.get_remaining_months()
        payment = self.current_payment.get()
        
        return self.calculate_amortization_schedule(balance, rate, remaining_months, payment, "Current Mortgage")
    
    def generate_scenario_schedule(self, scenario_index):
        """Generate amortization schedule for a refinance scenario"""
        scenario_vars = self.scenario_vars[scenario_index]
        
        balance = self.current_balance.get()
        rate = scenario_vars['rate'].get() / 100
        
        # Apply buydown if enabled
        if scenario_vars['use_points'].get():
            rate -= (scenario_vars['points'].get() * scenario_vars['point_reduction'].get() / 100)
        
        rate = rate / 12  # Monthly rate
        term_months = scenario_vars['term_years'].get() * 12
        
        # Calculate new payment
        if rate > 0:
            payment = balance * (rate * (1 + rate)**term_months) / ((1 + rate)**term_months - 1)
        else:
            payment = balance / term_months
            
        scenario_name = scenario_vars['name'].get()
        
        return self.calculate_amortization_schedule(balance, rate, term_months, payment, scenario_name)
    
    def calculate_amortization_schedule(self, principal, monthly_rate, num_payments, payment, scenario_name):
        """Calculate detailed amortization schedule"""
        schedule_data = []
        remaining_balance = principal
        
        for month in range(1, int(num_payments) + 1):
            # Calculate interest and principal for this payment
            interest_payment = remaining_balance * monthly_rate
            principal_payment = min(payment - interest_payment, remaining_balance)
            
            # Handle final payment
            if remaining_balance <= principal_payment:
                principal_payment = remaining_balance
                payment = principal_payment + interest_payment
                remaining_balance = 0
            else:
                remaining_balance -= principal_payment
            
            schedule_data.append({
                'Payment_Number': month,
                'Payment_Date': datetime.now().replace(day=1) + pd.DateOffset(months=month-1),
                'Beginning_Balance': remaining_balance + principal_payment,
                'Payment_Amount': payment,
                'Principal_Payment': principal_payment,
                'Interest_Payment': interest_payment,
                'Ending_Balance': remaining_balance,
                'Cumulative_Principal': principal - remaining_balance,
                'Cumulative_Interest': sum(row['Interest_Payment'] for row in schedule_data)
            })
            
            if remaining_balance <= 0:
                break
        
        df = pd.DataFrame(schedule_data)
        
        # Format currency columns
        currency_cols = ['Beginning_Balance', 'Payment_Amount', 'Principal_Payment', 
                        'Interest_Payment', 'Ending_Balance', 'Cumulative_Principal', 'Cumulative_Interest']
        
        for col in currency_cols:
            df[col] = df[col].round(2)
        
        # Format date column
        df['Payment_Date'] = df['Payment_Date'].dt.strftime('%Y-%m-%d')
        
        # Add scenario info as first row
        summary_row = pd.DataFrame([{
            'Payment_Number': f'SCENARIO: {scenario_name}',
            'Payment_Date': f'Rate: {monthly_rate*12*100:.3f}%',
            'Beginning_Balance': f'Original Balance: ${principal:,.2f}',
            'Payment_Amount': f'Monthly Payment: ${payment:,.2f}',
            'Principal_Payment': f'Total Payments: {len(schedule_data)}',
            'Interest_Payment': f'Total Interest: ${df["Cumulative_Interest"].iloc[-1]:,.2f}',
            'Ending_Balance': f'Total Cost: ${payment * len(schedule_data):,.2f}',
            'Cumulative_Principal': '',
            'Cumulative_Interest': ''
        }])
        
        # Add empty row
        empty_row = pd.DataFrame([{col: '' for col in df.columns}])
        
        # Combine summary, empty row, and schedule
        final_df = pd.concat([summary_row, empty_row, df], ignore_index=True)
        
        return final_df
    
    def show_help(self):
        """Show help information"""
        help_text = """
🏠 ENHANCED MORTGAGE REFINANCE CALCULATOR HELP

This calculator helps you determine if refinancing your mortgage makes financial sense by:

📊 TABS:
• Current Mortgage: Enter your existing loan details
• Refinance Scenarios: Set up different refi options to compare  
• Analysis Options: Choose market data and export settings
• Results: View detailed analysis and recommendations

💰 KEY FEATURES:
• Break-even analysis - when you recover closing costs
• Multiple scenario comparison
• Buydown points analysis 
• Real-time market data integration
• Expert forecast recommendations

🌐 MARKET DATA:
When enabled, scrapes current rates from:
• Freddie Mac PMMS
• Bankrate  
• Mortgage News Daily
Plus expert forecasts for timing recommendations.

🎯 BUYDOWN POINTS:
Check "Buy down with points" to analyze paying upfront to reduce your rate.
Typical: 1 point = 1% of loan amount, reduces rate by 0.25%

📄 EXPORT:
Results are saved as CSV files you can open in Excel for detailed analysis.

💡 TIPS:
• Use realistic rates from actual lender quotes
• Consider how long you'll stay in the home
• Factor in your risk tolerance and financial goals
        """
        
        help_window = tk.Toplevel(self.root)
        help_window.title("Help")
        help_window.geometry("600x500")
        
        help_text_widget = tk.Text(help_window, wrap=tk.WORD, font=('Arial', 10))
        help_scrollbar = ttk.Scrollbar(help_window, orient="vertical", command=help_text_widget.yview)
        help_text_widget.configure(yscrollcommand=help_scrollbar.set)
        
        help_text_widget.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        help_scrollbar.pack(side="right", fill="y", pady=10)
        
        help_text_widget.insert(tk.END, help_text)
        help_text_widget.config(state=tk.DISABLED)
    
    def show_error(self, message):
        """Show error message"""
        messagebox.showerror("Error", message)
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, f"❌ Error: {message}\n\n")
        self.results_text.insert(tk.END, "💡 Please check your inputs and try again.")
        self.results_text.config(state=tk.DISABLED)
    
    def run(self):
        """Start the GUI application"""
        self.root.mainloop()

def main():
    """Run the GUI mortgage calculator"""
    app = MortgageGUI()
    app.run()

if __name__ == "__main__":
    main()