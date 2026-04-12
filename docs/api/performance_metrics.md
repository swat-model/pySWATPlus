# PerformanceMetrics

`PerformanceMetrics` computes statistical performance indicators between simulated and observed time series.

**Available indicators:**

| Indicator | Full name | Direction |
|-----------|-----------|-----------|
| `NSE` | Nash–Sutcliffe Efficiency | Maximize (best = 1) |
| `KGE` | Kling–Gupta Efficiency | Maximize (best = 1) |
| `MSE` | Mean Squared Error | Minimize (best = 0) |
| `RMSE` | Root Mean Squared Error | Minimize (best = 0) |
| `PBIAS` | Percent Bias | Minimize (best = 0) |
| `MARE` | Mean Absolute Relative Error | Minimize (best = 0) |

```python
import pySWATPlus

pm = pySWATPlus.PerformanceMetrics()

# Compute directly from a simulation output file and an observed CSV
nse = pm.indicator_from_file(
    sim_file='/path/to/TxtInOut/channel_sd_day.txt',
    obs_file='/path/to/observed.csv',
    has_units=True,
    sim_col='flo_out',
    obs_col='discharge',
    indicator='NSE',
    date_format='%Y-%m-%d',
    apply_filter={'gis_id': [42]}
)
```

!!! warning
    Avoid `MARE` when the observed series contains zero values — it will cause division by zero.

---

::: pySWATPlus.PerformanceMetrics
