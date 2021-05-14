# Assignment3
## Application of factor investing
### step 1: calculate the mean and std(standard deviation) of iv(implied volatility) difference
For Calendar spread, there is arbitrage opportunity because the decay of time value of  nearby month contract is different from that of deferred month contract.

We can calculate the implied volatility of near month average options and far month average options in the last 20 trading days, and then calculate the mean and std according to the difference.We need to calculate the difference between the implied volatility of the far month average option and that of the near month average option on the trading day, and then compare it with mean+2*std and mean-2*std.

If iv_diff > mean+2*std, which means that the implied volatility of far month contract is at a high level. According to the knowledge we have learned, the higher implied volatility means the higher potential value, so we should short the deferred month option and long the nearby month option.
if iv_diff < mean-2*std, do the opposite.
Above mentioned is the opening signal, below is the closing signal.
If we open a position with iv_diff > mean+2*std, then the signal of closing a pisition is iv_diff < mean. If we open a position with iv_diff < mean+2*std, then the signal of closing a pisition is iv_diff > mean.That is to say, the requirements of opening the position will be more strict than closing the position.

We take July 1, 2016 to May 1, 2018 as the back test interval, and calculate all iv_diff. Then for each trading day, we use the IV of the 20 trading days before the trading day to calculate the mean and variance as the basis for the judgment of opening a position or closing a positions.The results are shown in the following figure.
![Image text](https://github.com/algo21-220040088/Assignment3/blob/main/result/pictures/iv_diff.png)

### step 2: back testing
According to the data obtained in the step 1, we can get all the opening and closing signals. If you sell the deferred month contract and buy the nearby month contract, it is marked as state=1. If you sell the nearby month contract and buy the deferred month contract, it is marked as state=-1. The result is shown in the figure below.
![Image text](https://github.com/algo21-220040088/Assignment3/blob/main/result/pictures/state.png)
