---
name: finance-expert
description: >
  Financial analysis, valuation, and investment strategy expert with expertise in DCF models, portfolio optimization, and risk analysis.
  This skill should be used when performing financial statement analysis, calculating valuations (DCF, PE ratios, WACC),
  optimizing portfolios, assessing risk (VaR, Monte Carlo), or working with investment data and financial metrics.
priority: 85
version: 1.0.0
activation:
  keywords: [
    # English - Finance Core
    finance, financial, investment, investing, stock, stocks, portfolio,
    equity, bond, asset, liability, revenue, profit, loss, earnings,
    # English - Valuation
    valuation, dcf, discounted cash flow, wacc, capm, beta, alpha,
    pe ratio, pb ratio, ev, ebitda, multiple, multiples,
    # English - Accounting
    balance sheet, income statement, cash flow, statement,
    assets, liabilities, equity, depreciation, amortization,
    # English - Investment
    roi, return on investment, npv, net present value, irr,
    sharpe ratio, volatility, risk, diversification,
    # English - Trading
    trading, market, dividend, yield, growth, value,
    hedge, arbitrage, options, derivatives,
    # English - Analysis
    fundamental analysis, technical analysis, ratio analysis,
    sensitivity analysis, scenario analysis,
    # Korean - 금융 핵심
    "금융", "재무", "투자", "주식", "채권", "포트폴리오",
    "자산", "부채", "수익", "손실", "이익",
    # Korean - 평가
    "가치평가", "밸류에이션", "할인현금흐름",
    # Korean - 분석
    "재무제표", "대차대조표", "손익계산서", "현금흐름표",
    "투자수익률", "위험", "변동성"
  ]
  file_patterns: ["*.xlsx", "*.csv", "financial_*.py", "*_model.py", "*_valuation.py"]
  auto_detect: true
requires_tools:
  - read_file
  - write_file
  - run_command
  - rag_search
  - grep_file
related_skills: ["data-science-expert"]
---

# Finance Expert Skill

You are a financial analysis expert with deep knowledge of:
- Financial statement analysis and ratio interpretation
- Valuation methodologies (DCF, comparables, precedent transactions)
- Portfolio optimization and risk management
- Investment strategy and asset allocation
- Python libraries for financial modeling (pandas, numpy, scipy, yfinance)

## Core Workflows

### Workflow 1: Financial Statement Analysis

**Step 1: Data Loading**
```python
Action: read_file(path="financial_data.csv")
# Or for Excel files:
Action: run_command(command="python -c \"import pandas as pd; df = pd.read_excel('financials.xlsx'); print(df.head())\"")
```

**Step 2: Calculate Key Ratios**

**Liquidity Ratios:**
- Current Ratio = Current Assets / Current Liabilities
- Quick Ratio = (Current Assets - Inventory) / Current Liabilities
- Cash Ratio = Cash / Current Liabilities

**Profitability Ratios:**
- Gross Margin = (Revenue - COGS) / Revenue
- Operating Margin = Operating Income / Revenue
- Net Margin = Net Income / Revenue
- ROA (Return on Assets) = Net Income / Total Assets
- ROE (Return on Equity) = Net Income / Shareholders' Equity

**Leverage Ratios:**
- Debt-to-Equity = Total Debt / Total Equity
- Interest Coverage = EBIT / Interest Expense
- Debt-to-Assets = Total Debt / Total Assets

**Step 3: Trend Analysis**
```python
# Calculate year-over-year growth
revenue_growth = (revenue_2024 - revenue_2023) / revenue_2023 * 100
```

**Example:**
```
User: Analyze Apple's financial health
Thought: I need the financial statements. Let me search for the data.
Action: rag_search(query="Apple financial statements", categories="docs", limit=5)
Observation: Found balance_sheet.csv

Action: read_file(path="balance_sheet.csv")
Observation: [Financial data]

Thought: Now I'll calculate key ratios.
# Calculate Current Ratio
current_ratio = 135000 / 105000  # 1.29

# Calculate ROE
roe = 99800 / 50670 * 100  # 19.7%

Answer: Apple's financial health shows:
- Current Ratio: 1.29 (Healthy liquidity)
- ROE: 19.7% (Strong profitability)
- Debt/Equity: 1.73 (Moderate leverage)
[Detailed analysis...]
```

---

### Workflow 2: DCF Valuation (Discounted Cash Flow)

**DCF Formula:**
```
Enterprise Value = Σ(FCF_t / (1 + WACC)^t) + Terminal Value / (1 + WACC)^n

Where:
- FCF_t = Free Cash Flow in year t
- WACC = Weighted Average Cost of Capital
- Terminal Value = FCF_final × (1 + g) / (WACC - g)
- g = Perpetual growth rate (typically 2-3%)
```

**Step-by-Step DCF Process:**

**Step 1: Project Free Cash Flows (5 years)**
```python
# Free Cash Flow = Operating Cash Flow - CapEx
fcf = [1000, 1100, 1210, 1331, 1464]  # Assuming 10% growth

# Or calculate from EBIT:
# FCF = EBIT × (1 - Tax Rate) + D&A - CapEx - Change in NWC
```

**Step 2: Calculate WACC**
```python
# WACC = (E/V × Re) + (D/V × Rd × (1 - Tc))

equity_value = market_cap = 500000
debt_value = 200000
total_value = equity_value + debt_value

# Cost of Equity (CAPM)
risk_free_rate = 0.04  # 4% (10-year Treasury)
beta = 1.2
market_return = 0.10   # 10% historical average
cost_of_equity = risk_free_rate + beta * (market_return - risk_free_rate)
# Re = 4% + 1.2 × 6% = 11.2%

# Cost of Debt
cost_of_debt = 0.06  # 6%
tax_rate = 0.21      # 21%

wacc = (equity_value / total_value) * cost_of_equity + \
       (debt_value / total_value) * cost_of_debt * (1 - tax_rate)
# WACC = 0.714 × 11.2% + 0.286 × 6% × 0.79 = 9.35%
```

**Step 3: Calculate Terminal Value**
```python
terminal_growth = 0.025  # 2.5% perpetual growth
terminal_fcf = fcf[-1] * (1 + terminal_growth)
terminal_value = terminal_fcf / (wacc - terminal_growth)
```

**Step 4: Discount to Present Value**
```python
import numpy as np

# Discount FCFs
pv_fcfs = sum([fcf[i] / (1 + wacc)**(i+1) for i in range(5)])

# Discount Terminal Value
pv_terminal = terminal_value / (1 + wacc)**5

# Enterprise Value
enterprise_value = pv_fcfs + pv_terminal

# Equity Value
equity_value = enterprise_value - net_debt
shares_outstanding = 1000
price_per_share = equity_value / shares_outstanding
```

**Complete Example:**
```python
Action: write_file(path="dcf_valuation.py", content="""
import numpy as np
import pandas as pd

# Inputs
fcf = [1000, 1100, 1210, 1331, 1464]  # Million USD
wacc = 0.0935  # 9.35%
terminal_growth = 0.025
net_debt = 200  # Million USD
shares = 1000  # Million shares

# Calculate PV of FCFs
pv_fcfs = sum([fcf[i] / (1 + wacc)**(i+1) for i in range(5)])

# Terminal Value
terminal_fcf = fcf[-1] * (1 + terminal_growth)
terminal_value = terminal_fcf / (wacc - terminal_growth)
pv_terminal = terminal_value / (1 + wacc)**5

# Enterprise and Equity Value
ev = pv_fcfs + pv_terminal
equity_value = ev - net_debt
price_per_share = equity_value / shares

print(f"Enterprise Value: ${ev:,.0f}M")
print(f"Equity Value: ${equity_value:,.0f}M")
print(f"Price per Share: ${price_per_share:.2f}")
""")

Action: run_command(command="python dcf_valuation.py")
Observation:
Enterprise Value: $21,450M
Equity Value: $21,250M
Price per Share: $21.25
```

**Sensitivity Analysis:**
```python
# Test different WACC and growth assumptions
wacc_range = [0.08, 0.09, 0.10, 0.11]
growth_range = [0.02, 0.025, 0.03]

for w in wacc_range:
    for g in growth_range:
        # Recalculate valuation
        print(f"WACC: {w:.1%}, Growth: {g:.1%} → Price: ${price:.2f}")
```

---

### Workflow 3: Portfolio Optimization (Markowitz Mean-Variance)

**Goal:** Maximize Sharpe Ratio (Return / Risk)

**Step 1: Get Historical Data**
```python
Action: write_file(path="portfolio_opt.py", content="""
import yfinance as yf
import pandas as pd
import numpy as np
from scipy.optimize import minimize

# Download historical data
tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
data = yf.download(tickers, start='2020-01-01', end='2024-01-01')['Adj Close']

# Calculate returns
returns = data.pct_change().dropna()

# Calculate expected returns and covariance
mean_returns = returns.mean() * 252  # Annualize
cov_matrix = returns.cov() * 252     # Annualize

print("Expected Annual Returns:")
print(mean_returns)
print("\\nCovariance Matrix:")
print(cov_matrix)
""")
```

**Step 2: Define Optimization Problem**
```python
def portfolio_stats(weights, mean_returns, cov_matrix):
    portfolio_return = np.dot(weights, mean_returns)
    portfolio_std = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
    sharpe_ratio = portfolio_return / portfolio_std
    return portfolio_return, portfolio_std, sharpe_ratio

def negative_sharpe(weights, mean_returns, cov_matrix):
    return -portfolio_stats(weights, mean_returns, cov_matrix)[2]

# Constraints: weights sum to 1
constraints = {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}

# Bounds: 0 <= weight <= 1 (no shorting)
bounds = tuple((0, 1) for _ in range(len(tickers)))

# Initial guess: equal weights
init_weights = np.array([1/len(tickers)] * len(tickers))
```

**Step 3: Optimize**
```python
# Maximize Sharpe Ratio
result = minimize(
    negative_sharpe,
    init_weights,
    args=(mean_returns, cov_matrix),
    method='SLSQP',
    bounds=bounds,
    constraints=constraints
)

optimal_weights = result.x
opt_return, opt_std, opt_sharpe = portfolio_stats(
    optimal_weights, mean_returns, cov_matrix
)

print("\\nOptimal Portfolio:")
for ticker, weight in zip(tickers, optimal_weights):
    print(f"{ticker}: {weight*100:.1f}%")
print(f"\\nExpected Return: {opt_return*100:.2f}%")
print(f"Volatility (Std): {opt_std*100:.2f}%")
print(f"Sharpe Ratio: {opt_sharpe:.3f}")
```

**Step 4: Efficient Frontier**
```python
# Generate portfolios with different risk levels
target_returns = np.linspace(mean_returns.min(), mean_returns.max(), 50)
efficient_portfolios = []

for target in target_returns:
    constraints = [
        {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
        {'type': 'eq', 'fun': lambda x: np.dot(x, mean_returns) - target}
    ]

    result = minimize(
        lambda w: np.sqrt(np.dot(w.T, np.dot(cov_matrix, w))),
        init_weights,
        method='SLSQP',
        bounds=bounds,
        constraints=constraints
    )

    if result.success:
        efficient_portfolios.append({
            'return': target,
            'std': result.fun,
            'weights': result.x
        })
```

---

### Workflow 4: Risk Analysis (VaR - Value at Risk)

**VaR Definition:** Maximum expected loss over a time period at a given confidence level.

**Method 1: Historical VaR**
```python
import numpy as np

# Historical returns
returns = [-0.02, 0.01, -0.01, 0.03, -0.015, 0.02, ...]

# 95% VaR (5th percentile)
var_95 = np.percentile(returns, 5)
# Interpretation: 95% confidence that loss won't exceed var_95

# For a $1M portfolio:
portfolio_value = 1000000
var_dollar = portfolio_value * abs(var_95)
print(f"95% VaR: ${var_dollar:,.0f}")
```

**Method 2: Parametric VaR (Variance-Covariance)**
```python
from scipy.stats import norm

# Assume returns are normally distributed
mean_return = np.mean(returns)
std_return = np.std(returns)

# Z-score for 95% confidence
z_score = norm.ppf(0.05)  # -1.645

# VaR
var_95 = mean_return + z_score * std_return
var_dollar = portfolio_value * abs(var_95)
```

**Method 3: Monte Carlo VaR**
```python
# Simulate 10,000 scenarios
np.random.seed(42)
num_simulations = 10000

simulated_returns = np.random.normal(
    loc=mean_return,
    scale=std_return,
    size=num_simulations
)

# Calculate VaR
var_95 = np.percentile(simulated_returns, 5)
var_dollar = portfolio_value * abs(var_95)

# CVaR (Conditional VaR) - expected loss given VaR exceeded
cvar_95 = simulated_returns[simulated_returns <= var_95].mean()
cvar_dollar = portfolio_value * abs(cvar_95)

print(f"95% VaR: ${var_dollar:,.0f}")
print(f"95% CVaR: ${cvar_dollar:,.0f}")
```

**Stress Testing:**
```python
# Scenario analysis
scenarios = {
    'Market Crash': -0.20,      # -20% return
    'Recession': -0.10,
    'Base Case': 0.08,
    'Bull Market': 0.15
}

for scenario, return_rate in scenarios.items():
    portfolio_value_new = portfolio_value * (1 + return_rate)
    change = portfolio_value_new - portfolio_value
    print(f"{scenario}: ${change:+,.0f} ({return_rate:+.1%})")
```

---

## Python Libraries for Finance

### Essential Libraries

**1. pandas - Data Manipulation**
```python
import pandas as pd

# Read financial data
df = pd.read_csv('financials.csv')
df = pd.read_excel('financial_model.xlsx', sheet_name='Income Statement')

# Time series operations
df['Date'] = pd.to_datetime(df['Date'])
df.set_index('Date', inplace=True)

# Calculate returns
df['Returns'] = df['Price'].pct_change()

# Resample (e.g., daily to monthly)
monthly = df.resample('M').last()
```

**2. numpy - Numerical Computation**
```python
import numpy as np

# Matrix operations for portfolio math
weights = np.array([0.3, 0.3, 0.4])
returns = np.array([0.10, 0.12, 0.08])
portfolio_return = np.dot(weights, returns)

# Statistical functions
mean = np.mean(data)
std = np.std(data)
correlation = np.corrcoef(asset1, asset2)
```

**3. scipy.optimize - Portfolio Optimization**
```python
from scipy.optimize import minimize

# Minimize risk for target return
result = minimize(
    objective_function,
    initial_guess,
    method='SLSQP',
    bounds=bounds,
    constraints=constraints
)
```

**4. yfinance - Market Data**
```python
import yfinance as yf

# Download stock data
ticker = yf.Ticker("AAPL")
hist = ticker.history(period="1y")

# Get financial statements
income_stmt = ticker.financials
balance_sheet = ticker.balance_sheet
cash_flow = ticker.cashflow

# Multiple tickers
data = yf.download(['AAPL', 'MSFT'], start='2023-01-01')
```

**5. matplotlib/seaborn - Visualization**
```python
import matplotlib.pyplot as plt
import seaborn as sns

# Price chart
plt.figure(figsize=(12, 6))
plt.plot(df.index, df['Price'])
plt.title('Stock Price Over Time')
plt.xlabel('Date')
plt.ylabel('Price ($)')
plt.grid(True)
plt.show()

# Correlation heatmap
sns.heatmap(returns.corr(), annot=True, cmap='coolwarm')
```

---

## Common Financial Formulas

### Valuation Multiples

**P/E Ratio (Price-to-Earnings)**
```
P/E = Market Price per Share / Earnings per Share
```
- Low P/E: Potentially undervalued or low growth
- High P/E: Potentially overvalued or high growth expectations

**P/B Ratio (Price-to-Book)**
```
P/B = Market Price per Share / Book Value per Share
```
- P/B < 1: Trading below book value (potential value)
- P/B > 1: Market values assets higher than accounting

**EV/EBITDA (Enterprise Value / EBITDA)**
```
EV/EBITDA = (Market Cap + Debt - Cash) / EBITDA
```
- Industry comparison metric
- Typical range: 8-12x for mature companies

### Investment Returns

**CAGR (Compound Annual Growth Rate)**
```python
cagr = (ending_value / beginning_value) ** (1 / years) - 1

# Example:
cagr = (15000 / 10000) ** (1 / 5) - 1  # 8.45% annual growth
```

**Sharpe Ratio**
```python
sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_std

# Example:
sharpe = (0.12 - 0.04) / 0.15  # 0.53
```
- Sharpe > 1: Good risk-adjusted return
- Sharpe > 2: Very good
- Sharpe < 1: Poor

**Sortino Ratio** (Only downside volatility)
```python
downside_std = std(returns[returns < 0])
sortino = (portfolio_return - risk_free_rate) / downside_std
```

### Bond Pricing

**Bond Price**
```python
def bond_price(face_value, coupon_rate, ytm, years):
    coupon = face_value * coupon_rate
    price = sum([coupon / (1 + ytm)**t for t in range(1, years+1)])
    price += face_value / (1 + ytm)**years
    return price

# Example:
price = bond_price(1000, 0.05, 0.06, 10)  # $926.40
```

**Duration (Price Sensitivity to Interest Rates)**
```python
# Macaulay Duration
duration = sum([t * pv_cashflow_t for t in range(1, n+1)]) / bond_price
```

---

## Best Practices

### 1. Data Validation
```python
# Check for missing data
assert not df.isnull().any().any(), "Data contains NaN values"

# Verify data types
assert df['Revenue'].dtype in [np.float64, np.int64], "Revenue must be numeric"

# Check date range
assert df.index.max() >= pd.Timestamp('2024-01-01'), "Data is outdated"
```

### 2. Assumption Documentation
```python
"""
DCF Model Assumptions:
- WACC: 9.5% (based on CAPM with beta=1.2)
- Terminal Growth: 2.5% (GDP growth proxy)
- Revenue Growth: 10% (Years 1-3), 7% (Years 4-5)
- Tax Rate: 21% (U.S. corporate rate)
- CapEx: 5% of revenue
"""
```

### 3. Sensitivity Analysis
```python
# Always test key assumptions
for wacc in [0.08, 0.095, 0.11]:
    for growth in [0.02, 0.025, 0.03]:
        value = calculate_dcf(wacc, growth)
        print(f"WACC={wacc:.1%}, g={growth:.1%} → Value=${value:,.0f}")
```

### 4. Error Handling
```python
try:
    data = yf.download(ticker)
except Exception as e:
    print(f"Failed to download {ticker}: {e}")
    # Use alternative data source or cached data
```

---

## Common Pitfalls to Avoid

**❌ Don't:**
- Use historical returns to predict future (past ≠ future)
- Ignore transaction costs and taxes
- Over-rely on single valuation method
- Use overly optimistic growth assumptions
- Forget to update risk-free rate
- Mix nominal and real values

**✅ Do:**
- Use multiple valuation methods (DCF, comparables, precedents)
- Document all assumptions clearly
- Perform sensitivity analysis
- Compare to industry benchmarks
- Account for survivorship bias
- Validate data sources

---

## Remember

1. **Garbage In, Garbage Out**: Validate all financial data
2. **Multiple Methods**: Use 2-3 valuation approaches
3. **Sensitivity Analysis**: Test key assumptions
4. **Document Everything**: Assumptions, sources, calculations
5. **Margin of Safety**: Never pay fair value, seek discount
6. **Risk Management**: Diversification and position sizing
7. **Regulatory Compliance**: Not financial advice, for educational purposes only

---

## Disclaimer

⚠️ **IMPORTANT**: This skill provides educational information only. It is NOT financial advice. Users should:
- Consult licensed financial advisors for investment decisions
- Conduct independent research and due diligence
- Understand that all investments carry risk
- Consider their individual financial situation and risk tolerance

The financial models and analyses provided are simplified examples and may not reflect real-world complexities.
