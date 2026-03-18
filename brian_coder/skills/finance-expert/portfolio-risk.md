# Portfolio Optimization & Risk

## Markowitz Mean-Variance
Maximize Sharpe Ratio = (Return - Rf) / Std

Steps: Historical returns → Covariance matrix → scipy.optimize.minimize(negative_sharpe)

## VaR (Value at Risk)
- **Historical**: np.percentile(returns, 5) for 95% VaR
- **Parametric**: mean + z_score × std (assumes normal)
- **Monte Carlo**: Simulate 10K scenarios → 5th percentile

## CVaR (Conditional VaR)
Expected loss given VaR exceeded: mean of returns below VaR threshold.

## Stress Testing
Test scenarios: Market Crash (-20%), Recession (-10%), Base (+8%), Bull (+15%)
