"""
=============================================================================
MOCK DATA GENERATORS UNIT TESTS
=============================================================================
Purpose: Unit tests for mock data generation utilities used in testing
Module: tests/mocks/data_generators.py

TEST CATEGORIES:
1. Financial Data Generation
2. Customer Data Generation  
3. Transaction Data Generation
4. Portfolio Data Generation
=============================================================================
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from decimal import Decimal
import random
import string
import re
import json

class FinancialDataGenerator:
    """Generate realistic financial data for testing."""
    
    def __init__(self, seed=42):
        """Initialize with optional random seed for reproducible tests."""
        self.seed = seed
        np.random.seed(seed)
        random.seed(seed)
    
    def generate_stock_prices(self, symbol, start_date, end_date, initial_price=100.0, volatility=0.02):
        """Generate realistic stock price time series using random walk."""
        start_dt = datetime.strptime(start_date, '%Y-%m-%d') if isinstance(start_date, str) else start_date
        end_dt = datetime.strptime(end_date, '%Y-%m-%d') if isinstance(end_date, str) else end_date
        
        # Generate business days
        business_days = pd.bdate_range(start=start_dt, end=end_dt)
        num_days = len(business_days)
        
        # Generate price movements using geometric Brownian motion
        returns = np.random.normal(0, volatility, num_days)
        prices = [initial_price]
        
        for i in range(1, num_days):
            price_change = prices[i-1] * returns[i]
            new_price = max(0.01, prices[i-1] + price_change)  # Prevent negative prices
            prices.append(new_price)
        
        return pd.DataFrame({
            'date': business_days,
            'symbol': symbol,
            'open': [p * np.random.uniform(0.99, 1.01) for p in prices],
            'high': [p * np.random.uniform(1.00, 1.05) for p in prices],
            'low': [p * np.random.uniform(0.95, 1.00) for p in prices],
            'close': prices,
            'volume': np.random.randint(100000, 10000000, num_days)
        })
    
    def generate_bond_data(self, count=100):
        """Generate synthetic bond portfolio data."""
        bond_types = ['CORPORATE', 'TREASURY', 'MUNICIPAL', 'AGENCY']
        credit_ratings = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC']
        
        bonds = []
        for i in range(count):
            bond_type = np.random.choice(bond_types)
            rating = np.random.choice(credit_ratings, p=[0.05, 0.15, 0.25, 0.30, 0.15, 0.08, 0.02])
            
            # Generate realistic yields based on rating and type
            base_yield = {
                'AAA': 0.02, 'AA': 0.025, 'A': 0.03, 'BBB': 0.035,
                'BB': 0.05, 'B': 0.08, 'CCC': 0.12
            }[rating]
            
            if bond_type == 'TREASURY':
                yield_spread = 0
            elif bond_type == 'AGENCY':
                yield_spread = np.random.uniform(0.001, 0.005)
            elif bond_type == 'CORPORATE':
                yield_spread = np.random.uniform(0.005, 0.02)
            else:  # MUNICIPAL
                yield_spread = np.random.uniform(0.002, 0.01)
            
            maturity_years = np.random.choice([1, 2, 3, 5, 7, 10, 15, 20, 30])
            maturity_date = datetime.now() + timedelta(days=maturity_years * 365)
            
            bond = {
                'bond_id': f'BOND{i+1:05d}',
                'issuer': f'{bond_type}_ISSUER_{i+1}',
                'bond_type': bond_type,
                'credit_rating': rating,
                'face_value': np.random.choice([1000, 5000, 10000, 25000]),
                'coupon_rate': base_yield + yield_spread + np.random.uniform(-0.005, 0.005),
                'maturity_date': maturity_date,
                'maturity_years': maturity_years,
                'current_price': np.random.uniform(85, 115),  # Price as percentage of face value
                'duration': np.random.uniform(0.8, 0.95) * maturity_years,  # Modified duration
                'yield_to_maturity': base_yield + yield_spread
            }
            bonds.append(bond)
        
        return pd.DataFrame(bonds)
    
    def generate_options_data(self, underlying_symbols, count=200):
        """Generate options contract data."""
        option_types = ['CALL', 'PUT']
        expiration_days = [7, 14, 30, 60, 90, 180, 365]
        
        options = []
        for i in range(count):
            underlying = np.random.choice(underlying_symbols)
            option_type = np.random.choice(option_types)
            
            # Generate realistic strike prices around current price
            current_price = np.random.uniform(50, 300)  # Mock current price
            strike_price = current_price * np.random.uniform(0.8, 1.2)
            
            days_to_expiry = np.random.choice(expiration_days)
            expiry_date = datetime.now() + timedelta(days=days_to_expiry)
            
            # Simple Black-Scholes approximation for option price
            volatility = np.random.uniform(0.15, 0.45)
            time_to_expiry = days_to_expiry / 365.0
            
            # Simplified option pricing (not actual Black-Scholes)
            moneyness = current_price / strike_price
            intrinsic_value = max(0, (current_price - strike_price) if option_type == 'CALL' 
                                 else (strike_price - current_price))
            time_value = volatility * np.sqrt(time_to_expiry) * current_price * 0.4
            option_price = intrinsic_value + time_value
            
            option = {
                'option_id': f'OPT{i+1:06d}',
                'underlying_symbol': underlying,
                'option_type': option_type,
                'strike_price': round(strike_price, 2),
                'expiry_date': expiry_date,
                'days_to_expiry': days_to_expiry,
                'current_price': round(option_price, 2),
                'underlying_price': round(current_price, 2),
                'volatility': round(volatility, 4),
                'delta': np.random.uniform(0.1, 0.9) if option_type == 'CALL' else np.random.uniform(-0.9, -0.1),
                'gamma': np.random.uniform(0.001, 0.05),
                'theta': np.random.uniform(-0.1, -0.001),
                'vega': np.random.uniform(0.01, 0.3)
            }
            options.append(option)
        
        return pd.DataFrame(options)
    
    def generate_fx_rates(self, currency_pairs, start_date, end_date):
        """Generate foreign exchange rate time series."""
        start_dt = datetime.strptime(start_date, '%Y-%m-%d') if isinstance(start_date, str) else start_date
        end_dt = datetime.strptime(end_date, '%Y-%m-%d') if isinstance(end_date, str) else end_date
        
        # Generate daily rates (including weekends for FX)
        date_range = pd.date_range(start=start_dt, end=end_dt, freq='D')
        
        fx_data = []
        for pair in currency_pairs:
            # Set realistic initial rates
            initial_rates = {
                'EUR/USD': 1.1000, 'GBP/USD': 1.3000, 'USD/JPY': 110.0,
                'USD/CHF': 0.9200, 'AUD/USD': 0.7500, 'USD/CAD': 1.2500
            }
            
            initial_rate = initial_rates.get(pair, 1.0000)
            volatility = 0.005  # 0.5% daily volatility
            
            rates = [initial_rate]
            for i in range(1, len(date_range)):
                change = np.random.normal(0, volatility)
                new_rate = rates[i-1] * (1 + change)
                rates.append(new_rate)
            
            for i, dt in enumerate(date_range):
                fx_data.append({
                    'date': dt,
                    'currency_pair': pair,
                    'rate': round(rates[i], 4),
                    'bid': round(rates[i] * 0.9998, 4),  # Small bid-ask spread
                    'ask': round(rates[i] * 1.0002, 4)
                })
        
        return pd.DataFrame(fx_data)


class CustomerDataGenerator:
    """Generate customer and account data for testing."""
    
    def __init__(self, seed=42):
        self.seed = seed
        np.random.seed(seed)
        random.seed(seed)
    
    def generate_customers(self, count=1000):
        """Generate customer demographic data."""
        first_names = ['John', 'Jane', 'Michael', 'Sarah', 'David', 'Lisa', 'Robert', 'Mary', 
                      'James', 'Patricia', 'William', 'Jennifer', 'Richard', 'Elizabeth']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 
                     'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez']
        
        states = ['CA', 'NY', 'TX', 'FL', 'IL', 'PA', 'OH', 'GA', 'NC', 'MI']
        account_types = ['INDIVIDUAL', 'JOINT', 'CORPORATE', 'TRUST', 'IRA']
        risk_profiles = ['CONSERVATIVE', 'MODERATE', 'AGGRESSIVE']
        
        customers = []
        for i in range(count):
            # Generate birth date (18-80 years old)
            age = np.random.randint(18, 81)
            birth_date = datetime.now() - timedelta(days=age * 365 + np.random.randint(-180, 180))
            
            # Generate income based on age and other factors
            base_income = np.random.lognormal(mean=10.5, sigma=0.7)  # Log-normal distribution
            income = max(25000, min(500000, base_income))  # Cap between 25K and 500K
            
            customer = {
                'customer_id': f'CUST{i+1:06d}',
                'first_name': np.random.choice(first_names),
                'last_name': np.random.choice(last_names),
                'birth_date': birth_date.date(),
                'age': age,
                'email': f'customer{i+1}@email.com',
                'phone': f'({np.random.randint(200,999)}) {np.random.randint(200,999)}-{np.random.randint(1000,9999)}',
                'state': np.random.choice(states),
                'zip_code': f'{np.random.randint(10000, 99999)}',
                'account_type': np.random.choice(account_types, p=[0.4, 0.25, 0.15, 0.1, 0.1]),
                'annual_income': round(income, 2),
                'net_worth': round(income * np.random.uniform(2, 8), 2),
                'risk_profile': np.random.choice(risk_profiles, p=[0.3, 0.5, 0.2]),
                'investment_experience': np.random.choice(['NOVICE', 'INTERMEDIATE', 'ADVANCED'], p=[0.3, 0.5, 0.2]),
                'account_opened_date': datetime.now() - timedelta(days=np.random.randint(30, 2000)),
                'is_accredited': income > 200000 or (income > 100000 and np.random.random() < 0.3)
            }
            customers.append(customer)
        
        return pd.DataFrame(customers)
    
    def generate_accounts(self, customer_ids, accounts_per_customer=1.5):
        """Generate account data for customers."""
        account_types = ['CHECKING', 'SAVINGS', 'INVESTMENT', 'RETIREMENT', 'TRADING']
        account_status = ['ACTIVE', 'INACTIVE', 'CLOSED']
        
        accounts = []
        account_id = 1
        
        for customer_id in customer_ids:
            # Determine number of accounts for this customer
            num_accounts = max(1, int(np.random.poisson(accounts_per_customer)))
            
            for _ in range(num_accounts):
                account_type = np.random.choice(account_types)
                
                # Generate realistic balance based on account type
                if account_type == 'CHECKING':
                    balance = np.random.uniform(500, 25000)
                elif account_type == 'SAVINGS':
                    balance = np.random.uniform(1000, 100000)
                elif account_type == 'INVESTMENT':
                    balance = np.random.lognormal(mean=10, sigma=1.5)  # Wide range
                elif account_type == 'RETIREMENT':
                    balance = np.random.uniform(10000, 500000)
                else:  # TRADING
                    balance = np.random.uniform(5000, 200000)
                
                account = {
                    'account_id': f'ACC{account_id:08d}',
                    'customer_id': customer_id,
                    'account_type': account_type,
                    'account_status': np.random.choice(account_status, p=[0.85, 0.1, 0.05]),
                    'balance': round(balance, 2),
                    'opened_date': datetime.now() - timedelta(days=np.random.randint(30, 1500)),
                    'last_activity_date': datetime.now() - timedelta(days=np.random.randint(0, 90)),
                    'monthly_fee': 0 if account_type in ['INVESTMENT', 'TRADING'] else np.random.choice([0, 5, 10, 15]),
                    'interest_rate': self._get_interest_rate(account_type),
                    'minimum_balance': self._get_minimum_balance(account_type)
                }
                accounts.append(account)
                account_id += 1
        
        return pd.DataFrame(accounts)
    
    def _get_interest_rate(self, account_type):
        """Get realistic interest rate for account type."""
        rates = {
            'CHECKING': np.random.uniform(0.001, 0.01),
            'SAVINGS': np.random.uniform(0.005, 0.025),
            'INVESTMENT': 0.0,  # Investment accounts don't have interest rates
            'RETIREMENT': 0.0,
            'TRADING': 0.0
        }
        return round(rates.get(account_type, 0.0), 4)
    
    def _get_minimum_balance(self, account_type):
        """Get minimum balance requirement for account type."""
        minimums = {
            'CHECKING': np.random.choice([0, 100, 500, 1000]),
            'SAVINGS': np.random.choice([0, 100, 500]),
            'INVESTMENT': np.random.choice([1000, 2500, 5000]),
            'RETIREMENT': np.random.choice([0, 1000]),
            'TRADING': np.random.choice([2000, 5000, 10000])
        }
        return minimums.get(account_type, 0)


class TransactionDataGenerator:
    """Generate transaction data for testing."""
    
    def __init__(self, seed=42):
        self.seed = seed
        np.random.seed(seed)
        random.seed(seed)
    
    def generate_transactions(self, account_ids, start_date, end_date, transactions_per_day=50):
        """Generate realistic transaction data."""
        start_dt = datetime.strptime(start_date, '%Y-%m-%d') if isinstance(start_date, str) else start_date
        end_dt = datetime.strptime(end_date, '%Y-%m-%d') if isinstance(end_date, str) else end_date
        
        transaction_types = {
            'DEPOSIT': {'weight': 0.15, 'amount_range': (50, 5000), 'sign': 1},
            'WITHDRAWAL': {'weight': 0.20, 'amount_range': (20, 2000), 'sign': -1},
            'TRANSFER_IN': {'weight': 0.10, 'amount_range': (100, 10000), 'sign': 1},
            'TRANSFER_OUT': {'weight': 0.10, 'amount_range': (100, 10000), 'sign': -1},
            'BUY': {'weight': 0.15, 'amount_range': (500, 50000), 'sign': -1},
            'SELL': {'weight': 0.15, 'amount_range': (500, 50000), 'sign': 1},
            'DIVIDEND': {'weight': 0.05, 'amount_range': (10, 1000), 'sign': 1},
            'INTEREST': {'weight': 0.05, 'amount_range': (1, 100), 'sign': 1},
            'FEE': {'weight': 0.05, 'amount_range': (5, 50), 'sign': -1}
        }
        
        # Create weighted list for transaction type selection
        type_weights = [info['weight'] for info in transaction_types.values()]
        type_names = list(transaction_types.keys())
        
        transactions = []
        transaction_id = 1
        
        # Generate transactions for each day
        current_date = start_dt
        while current_date <= end_dt:
            # Vary number of transactions per day
            daily_transactions = max(1, int(np.random.poisson(transactions_per_day)))
            
            for _ in range(daily_transactions):
                txn_type = np.random.choice(type_names, p=type_weights)
                txn_info = transaction_types[txn_type]
                
                # Generate transaction amount
                min_amt, max_amt = txn_info['amount_range']
                amount = np.random.uniform(min_amt, max_amt) * txn_info['sign']
                
                # Add timestamp variation throughout the day
                hour = np.random.randint(9, 17)  # Business hours
                minute = np.random.randint(0, 60)
                second = np.random.randint(0, 60)
                
                transaction_time = current_date.replace(hour=hour, minute=minute, second=second)
                
                transaction = {
                    'transaction_id': f'TXN{transaction_id:010d}',
                    'account_id': np.random.choice(account_ids),
                    'transaction_type': txn_type,
                    'amount': round(amount, 2),
                    'transaction_date': transaction_time,
                    'description': self._generate_description(txn_type),
                    'reference_number': f'REF{np.random.randint(100000, 999999)}',
                    'status': np.random.choice(['COMPLETED', 'PENDING', 'FAILED'], p=[0.95, 0.04, 0.01]),
                    'channel': np.random.choice(['ONLINE', 'MOBILE', 'BRANCH', 'ATM', 'PHONE'], p=[0.4, 0.3, 0.15, 0.1, 0.05])
                }
                
                # Add specific fields for investment transactions
                if txn_type in ['BUY', 'SELL']:
                    transaction.update({
                        'symbol': np.random.choice(['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'SPY', 'QQQ']),
                        'quantity': np.random.randint(1, 1000),
                        'price': round(abs(amount) / np.random.randint(1, 1000), 2)
                    })
                
                transactions.append(transaction)
                transaction_id += 1
            
            current_date += timedelta(days=1)
        
        return pd.DataFrame(transactions)
    
    def _generate_description(self, transaction_type):
        """Generate realistic transaction descriptions."""
        descriptions = {
            'DEPOSIT': ['Direct Deposit Payroll', 'Cash Deposit', 'Check Deposit', 'Mobile Deposit'],
            'WITHDRAWAL': ['ATM Withdrawal', 'Cash Withdrawal', 'Bill Payment', 'Online Purchase'],
            'TRANSFER_IN': ['Internal Transfer Credit', 'Wire Transfer In', 'ACH Credit'],
            'TRANSFER_OUT': ['Internal Transfer Debit', 'Wire Transfer Out', 'ACH Debit'],
            'BUY': ['Stock Purchase', 'ETF Purchase', 'Mutual Fund Purchase', 'Bond Purchase'],
            'SELL': ['Stock Sale', 'ETF Sale', 'Mutual Fund Sale', 'Bond Sale'],
            'DIVIDEND': ['Dividend Payment', 'Distribution', 'Interest Income'],
            'INTEREST': ['Account Interest', 'Savings Interest', 'Interest Credit'],
            'FEE': ['Monthly Fee', 'Transaction Fee', 'Overdraft Fee', 'Wire Fee']
        }
        
        return np.random.choice(descriptions.get(transaction_type, ['Transaction']))


class PortfolioDataGenerator:
    """Generate portfolio and holdings data for testing."""
    
    def __init__(self, seed=42):
        self.seed = seed
        np.random.seed(seed)
        random.seed(seed)
    
    def generate_portfolios(self, customer_ids, portfolios_per_customer=1.2):
        """Generate investment portfolio data."""
        portfolio_types = ['INDIVIDUAL', 'JOINT', 'IRA', 'ROTH_IRA', '401K', 'TRUST']
        investment_objectives = ['GROWTH', 'INCOME', 'BALANCED', 'CAPITAL_PRESERVATION', 'AGGRESSIVE_GROWTH']
        
        portfolios = []
        portfolio_id = 1
        
        for customer_id in customer_ids:
            num_portfolios = max(1, int(np.random.poisson(portfolios_per_customer)))
            
            for _ in range(num_portfolios):
                portfolio_type = np.random.choice(portfolio_types)
                objective = np.random.choice(investment_objectives)
                
                # Generate realistic portfolio value
                portfolio_value = np.random.lognormal(mean=11, sigma=1.2)
                portfolio_value = max(1000, min(5000000, portfolio_value))
                
                portfolio = {
                    'portfolio_id': f'PORT{portfolio_id:06d}',
                    'customer_id': customer_id,
                    'portfolio_type': portfolio_type,
                    'investment_objective': objective,
                    'total_value': round(portfolio_value, 2),
                    'cash_balance': round(portfolio_value * np.random.uniform(0.02, 0.15), 2),
                    'created_date': datetime.now() - timedelta(days=np.random.randint(30, 1500)),
                    'last_rebalanced': datetime.now() - timedelta(days=np.random.randint(0, 365)),
                    'risk_tolerance': np.random.choice(['LOW', 'MEDIUM', 'HIGH'], p=[0.3, 0.5, 0.2]),
                    'benchmark': self._get_benchmark(objective),
                    'management_fee': round(np.random.uniform(0.25, 1.50), 2)  # Annual fee percentage
                }
                portfolios.append(portfolio)
                portfolio_id += 1
        
        return pd.DataFrame(portfolios)
    
    def generate_holdings(self, portfolio_ids):
        """Generate portfolio holdings data."""
        asset_classes = ['EQUITY', 'BOND', 'ETF', 'MUTUAL_FUND', 'REIT', 'COMMODITY']
        equity_symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA', 'JPM', 'JNJ', 'PG']
        bond_types = ['CORPORATE', 'TREASURY', 'MUNICIPAL']
        etf_symbols = ['SPY', 'QQQ', 'IWM', 'VTI', 'BND', 'GLD', 'VEA', 'VWO']
        
        holdings = []
        holding_id = 1
        
        for portfolio_id in portfolio_ids:
            # Generate 5-15 holdings per portfolio
            num_holdings = np.random.randint(5, 16)
            
            # Ensure asset allocation sums close to 100%
            allocations = np.random.dirichlet(np.ones(num_holdings))
            
            for i in range(num_holdings):
                asset_class = np.random.choice(asset_classes, p=[0.4, 0.2, 0.2, 0.1, 0.05, 0.05])
                
                # Generate symbol based on asset class
                if asset_class == 'EQUITY':
                    symbol = np.random.choice(equity_symbols)
                elif asset_class == 'ETF':
                    symbol = np.random.choice(etf_symbols)
                elif asset_class == 'BOND':
                    bond_type = np.random.choice(bond_types)
                    symbol = f'{bond_type}_BOND_{np.random.randint(1, 100)}'
                else:
                    symbol = f'{asset_class}_{np.random.randint(1, 50)}'
                
                # Generate position details
                current_price = np.random.uniform(10, 500)
                allocation_pct = allocations[i] * 100
                
                # Calculate shares from allocation
                portfolio_value = np.random.uniform(50000, 500000)  # Mock portfolio value
                position_value = portfolio_value * allocations[i]
                shares = position_value / current_price
                
                holding = {
                    'holding_id': f'HOLD{holding_id:08d}',
                    'portfolio_id': portfolio_id,
                    'symbol': symbol,
                    'asset_class': asset_class,
                    'shares': round(shares, 6),
                    'current_price': round(current_price, 2),
                    'market_value': round(position_value, 2),
                    'cost_basis': round(current_price * np.random.uniform(0.8, 1.2), 2),
                    'allocation_percentage': round(allocation_pct, 2),
                    'purchase_date': datetime.now() - timedelta(days=np.random.randint(1, 1000)),
                    'last_updated': datetime.now() - timedelta(hours=np.random.randint(1, 48)),
                    'unrealized_gain_loss': round(position_value * np.random.uniform(-0.3, 0.5), 2),
                    'sector': self._get_sector(asset_class) if asset_class == 'EQUITY' else None
                }
                holdings.append(holding)
                holding_id += 1
        
        return pd.DataFrame(holdings)
    
    def _get_benchmark(self, objective):
        """Get appropriate benchmark for investment objective."""
        benchmarks = {
            'GROWTH': 'S&P 500',
            'INCOME': 'Barclays Aggregate Bond',
            'BALANCED': '60/40 Stock/Bond',
            'CAPITAL_PRESERVATION': 'Treasury Bills',
            'AGGRESSIVE_GROWTH': 'Russell 2000'
        }
        return benchmarks.get(objective, 'S&P 500')
    
    def _get_sector(self, asset_class):
        """Get sector for equity holdings."""
        if asset_class != 'EQUITY':
            return None
        
        sectors = ['Technology', 'Healthcare', 'Financial', 'Consumer Discretionary', 
                  'Industrial', 'Communication', 'Consumer Staples', 'Energy', 
                  'Utilities', 'Real Estate', 'Materials']
        return np.random.choice(sectors)


class TestFinancialDataGenerator:
    @pytest.fixture
    def generator(self):
        return FinancialDataGenerator(seed=42)
    
    @pytest.mark.unit
    def test_stock_price_generation(self, generator):
        df = generator.generate_stock_prices('AAPL', '2024-01-01', '2024-01-31', initial_price=150.0)
        
        assert len(df) > 0
        assert 'date' in df.columns
        assert 'symbol' in df.columns
        assert all(df['symbol'] == 'AAPL')
        assert 'open' in df.columns and 'high' in df.columns and 'low' in df.columns and 'close' in df.columns
        
        # Check price relationships
        assert all(df['high'] >= df['low'])
        assert all(df['high'] >= df['close'])
        assert all(df['low'] <= df['close'])
        
        # Check prices are positive
        assert all(df['close'] > 0)
    
    @pytest.mark.unit
    def test_bond_data_generation(self, generator):
        df = generator.generate_bond_data(count=50)
        
        assert len(df) == 50
        assert 'bond_id' in df.columns
        assert 'bond_type' in df.columns
        assert 'credit_rating' in df.columns
        
        # Check rating validity
        valid_ratings = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC']
        assert all(df['credit_rating'].isin(valid_ratings))
        
        # Check yield relationships (higher risk = higher yield generally)
        aaa_bonds = df[df['credit_rating'] == 'AAA']
        ccc_bonds = df[df['credit_rating'] == 'CCC']
        if len(aaa_bonds) > 0 and len(ccc_bonds) > 0:
            assert aaa_bonds['yield_to_maturity'].mean() < ccc_bonds['yield_to_maturity'].mean()
    
    @pytest.mark.unit
    def test_options_data_generation(self, generator):
        symbols = ['AAPL', 'GOOGL', 'MSFT']
        df = generator.generate_options_data(symbols, count=100)
        
        assert len(df) == 100
        assert 'option_id' in df.columns
        assert 'option_type' in df.columns
        assert all(df['option_type'].isin(['CALL', 'PUT']))
        assert all(df['underlying_symbol'].isin(symbols))
        
        # Check Greeks are in reasonable ranges
        assert all(df['delta'].between(-1, 1))
        assert all(df['gamma'] >= 0)
        assert all(df['theta'] <= 0)
        assert all(df['vega'] >= 0)
    
    @pytest.mark.unit
    def test_fx_rates_generation(self, generator):
        pairs = ['EUR/USD', 'GBP/USD']
        df = generator.generate_fx_rates(pairs, '2024-01-01', '2024-01-10')
        
        assert len(df) > 0
        assert 'currency_pair' in df.columns
        assert 'rate' in df.columns
        assert all(df['currency_pair'].isin(pairs))
        
        # Check bid-ask spread
        assert all(df['bid'] <= df['rate'])
        assert all(df['ask'] >= df['rate'])
        assert all((df['ask'] - df['bid']) > 0)  # Positive spread


class TestCustomerDataGenerator:
    @pytest.fixture
    def generator(self):
        return CustomerDataGenerator(seed=42)
    
    @pytest.mark.unit
    def test_customer_generation(self, generator):
        df = generator.generate_customers(count=100)
        
        assert len(df) == 100
        assert 'customer_id' in df.columns
        assert 'first_name' in df.columns
        assert 'annual_income' in df.columns
        
        # Check age consistency
        assert all(df['age'] >= 18)
        assert all(df['age'] <= 80)
        
        # Check income ranges
        assert all(df['annual_income'] >= 25000)
        assert all(df['annual_income'] <= 500000)
        
        # Check email format
        assert all('@' in email for email in df['email'])
    
    @pytest.mark.unit
    def test_account_generation(self, generator):
        customer_ids = [f'CUST{i:06d}' for i in range(1, 11)]
        df = generator.generate_accounts(customer_ids)
        
        assert len(df) > 0
        assert 'account_id' in df.columns
        assert 'customer_id' in df.columns
        assert all(df['customer_id'].isin(customer_ids))
        
        # Check account types
        valid_types = ['CHECKING', 'SAVINGS', 'INVESTMENT', 'RETIREMENT', 'TRADING']
        assert all(df['account_type'].isin(valid_types))
        
        # Check balance is positive
        assert all(df['balance'] >= 0)


class TestTransactionDataGenerator:
    @pytest.fixture
    def generator(self):
        return TransactionDataGenerator(seed=42)
    
    @pytest.mark.unit
    def test_transaction_generation(self, generator):
        account_ids = [f'ACC{i:08d}' for i in range(1, 6)]
        df = generator.generate_transactions(account_ids, '2024-01-01', '2024-01-05')
        
        assert len(df) > 0
        assert 'transaction_id' in df.columns
        assert 'account_id' in df.columns
        assert all(df['account_id'].isin(account_ids))
        
        # Check transaction types
        expected_types = ['DEPOSIT', 'WITHDRAWAL', 'TRANSFER_IN', 'TRANSFER_OUT', 
                         'BUY', 'SELL', 'DIVIDEND', 'INTEREST', 'FEE']
        assert all(df['transaction_type'].isin(expected_types))
        
        # Check investment transactions have additional fields
        investment_txns = df[df['transaction_type'].isin(['BUY', 'SELL'])]
        if len(investment_txns) > 0:
            assert 'symbol' in investment_txns.columns
            assert 'quantity' in investment_txns.columns


class TestPortfolioDataGenerator:
    @pytest.fixture
    def generator(self):
        return PortfolioDataGenerator(seed=42)
    
    @pytest.mark.unit
    def test_portfolio_generation(self, generator):
        customer_ids = [f'CUST{i:06d}' for i in range(1, 11)]
        df = generator.generate_portfolios(customer_ids)
        
        assert len(df) > 0
        assert 'portfolio_id' in df.columns
        assert 'customer_id' in df.columns
        assert all(df['customer_id'].isin(customer_ids))
        
        # Check portfolio values are reasonable
        assert all(df['total_value'] >= 1000)
        assert all(df['cash_balance'] >= 0)
        assert all(df['cash_balance'] <= df['total_value'])
    
    @pytest.mark.unit
    def test_holdings_generation(self, generator):
        portfolio_ids = [f'PORT{i:06d}' for i in range(1, 6)]
        df = generator.generate_holdings(portfolio_ids)
        
        assert len(df) > 0
        assert 'holding_id' in df.columns
        assert 'portfolio_id' in df.columns
        assert all(df['portfolio_id'].isin(portfolio_ids))
        
        # Check asset classes
        valid_classes = ['EQUITY', 'BOND', 'ETF', 'MUTUAL_FUND', 'REIT', 'COMMODITY']
        assert all(df['asset_class'].isin(valid_classes))
        
        # Check shares and prices are positive
        assert all(df['shares'] > 0)
        assert all(df['current_price'] > 0)
        assert all(df['market_value'] > 0)
    
    @pytest.mark.integration
    def test_complete_data_generation_workflow(self):
        """Test complete workflow of generating related financial data."""
        # Initialize generators
        customer_gen = CustomerDataGenerator(seed=42)
        account_gen = CustomerDataGenerator(seed=42)
        transaction_gen = TransactionDataGenerator(seed=42)
        portfolio_gen = PortfolioDataGenerator(seed=42)
        financial_gen = FinancialDataGenerator(seed=42)
        
        # Generate customers
        customers = customer_gen.generate_customers(count=10)
        customer_ids = customers['customer_id'].tolist()
        
        # Generate accounts
        accounts = account_gen.generate_accounts(customer_ids)
        account_ids = accounts['account_id'].tolist()
        
        # Generate transactions
        transactions = transaction_gen.generate_transactions(account_ids, '2024-01-01', '2024-01-07')
        
        # Generate portfolios and holdings
        portfolios = portfolio_gen.generate_portfolios(customer_ids)
        portfolio_ids = portfolios['portfolio_id'].tolist()
        holdings = portfolio_gen.generate_holdings(portfolio_ids)
        
        # Generate market data
        symbols = ['AAPL', 'GOOGL', 'MSFT']
        stock_prices = financial_gen.generate_stock_prices('AAPL', '2024-01-01', '2024-01-10')
        
        # Verify relationships
        assert len(accounts) >= len(customers)  # Multiple accounts per customer possible
        assert all(accounts['customer_id'].isin(customer_ids))
        assert all(transactions['account_id'].isin(account_ids))
        assert all(holdings['portfolio_id'].isin(portfolio_ids))
        
        # Verify data quality
        assert len(transactions) > 0
        assert len(holdings) > 0
        assert len(stock_prices) > 0