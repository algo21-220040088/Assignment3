# Assignment3
## Application of factor investing
### step 1: calculate the mean and std(standard deviation) of iv(implied volatility) difference
For Calendar spread, there is arbitrage opportunity because the decay of time value of  nearby month contract is different from that of deferred month contract.

We can calculate the implied volatility of near month average options and far month average options in the last 20 trading days, and then calculate the mean and std according to the difference.We need to calculate the difference between the implied volatility of the far month average option and that of the near month average option on the trading day, and then compare it with mean+2*std and mean-2*std.

If iv_diff > mean+2*std, which means that the implied volatility of far month contract is at a high level. According to the knowledge we have learned, the higher implied volatility means the higher potential value, so we should short the deferred month option and long the nearby month option.
if iv_diff < mean-2*std, do the opposite.
Above mentioned is the opening signal, below is the closing signal.
If we open a position with iv_diff > mean+2*std, then the signal of closing a pisition is iv_diff < mean. If we open a position with iv_diff < mean+2*std, then the signal of closing a pisition is iv_diff > mean.That is to say, the requirements of opening the position will be more strict than closing the position.
