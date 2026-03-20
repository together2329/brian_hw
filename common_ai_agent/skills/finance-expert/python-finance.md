# Python Finance Libraries

## pandas — Data manipulation
```python
df = pd.read_csv('data.csv')          # or pd.read_excel()
df['Returns'] = df['Price'].pct_change()
monthly = df.resample('M').last()
```

## numpy — Matrix operations
```python
portfolio_return = np.dot(weights, returns)
portfolio_std = np.sqrt(np.dot(w.T, np.dot(cov_matrix, w)))
```

## scipy.optimize — Portfolio optimization
```python
from scipy.optimize import minimize
result = minimize(objective, init_weights, method='SLSQP', bounds=bounds, constraints=constraints)
```

## yfinance — Market data
```python
ticker = yf.Ticker("AAPL")
hist = ticker.history(period="1y")
financials = ticker.financials
```

## Bond pricing
```python
price = sum(coupon/(1+ytm)**t for t in range(1, years+1)) + face/(1+ytm)**years
```
