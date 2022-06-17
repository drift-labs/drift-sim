import pandas as pd
import numpy as np
from dataclasses import dataclass, field
import os

@dataclass
class Oracle:
    prices: list[float]
    timestamps: list[int] 

    def __init__(self, path=None, prices=None, timestamps=None):
        if path is not None:
            oracle_df = pd.read_csv(path, nrows=300) #todo
            self.prices = oracle_df['price'].values
            self.timestamps = oracle_df['timestamp'].values

        if prices is not None:
            self.prices = prices

        if timestamps is not None:
            self.timestamps = timestamps
            
    def __len__(self):
        return int(max(self.timestamps))
    
    def get_timestamp_range(self):
        return int(min(self.timestamps)), int(max(self.timestamps))

    def get_price(self, timestamp):
        # oracle is price[i] from timestamp[i] to but not including timestamp[i+1]
        # prices = [0, 1, 2]
        # timestapmes = [0, 1, 2]
        # price(0) = 0
        # price(1) = 1
        # price(2) = 2
        time_difference = self.timestamps - timestamp
        min_dist_index = np.absolute(time_difference).argmin()
        # only before (ie timestamps[idx] <= timestamp)
        if time_difference[min_dist_index] > 0: 
            min_dist_index -= 1    
        
        price = self.prices[min_dist_index]
        assert(price >= 0)
        return price 

    def to_csv(self, path):
        assert('oracle_prices.csv' in path)
        
        oracle_df = pd.DataFrame({'timestamp': self.timestamps, 'price': self.prices})
        oracle_df.to_csv(path, index=False)

        max_t = max(self.timestamps)
        all_timestamps = list(range(max_t))
        all_prices = [int(self.get_price(t) * 1e10) for t in all_timestamps]

        # save to file -- easier to cross reference with per-timestamp prices  
        oracle_df = pd.DataFrame({'timestamp': all_timestamps, 'price': all_prices})
        oracle_df.to_csv(os.path.dirname(path)+"/all_oracle_prices.csv", index=False)
