import numpy as np 
import json

import sys
sys.path.insert(0, '../driftpy/src/')
sys.path.insert(0, '../')

from driftpy.math.amm import *
from driftpy.math.trade import *
from driftpy.math.positions import *
from driftpy.math.market import *
from driftpy.math.user import *

from sim.events import * 
from sim.agents import * 

# %%
def random_walk_oracle(start_price, n_steps=100):
    prices = []
    timestamps = []
    
    price = start_price
    time = 0     
    for _ in range(n_steps):
        prices.append(price)
        timestamps.append(time)

        sign = np.random.choice([-1, 1])
        price = price + sign * np.random.normal()
        time = time + np.random.randint(low=1, high=10)

    # normalize prices 
    prices = np.array(prices)
    # lowest price = $1
    prices = prices - np.min(prices) + 1
    
    timestamps = np.array(timestamps)
        
    return prices, timestamps


def rand_heterosk_oracle(start_price, n_steps=100):
    prices = []
    timestamps = []
    
    k_period = 10 # 10 seconds
    price = start_price
    time = 0     
    std = 1
    for _ in range(n_steps):
        prices.append(price)
        timestamps.append(time)

        sign = np.random.choice([-1, 1])
        if np.random.randint(low=1, high=9) > 7:
            price_delta = sign * abs(np.random.normal(scale=1))
        else:
            price_delta = sign * abs(np.random.normal(scale=std))

        time_delta = np.random.randint(low=1, high=9)

        std = np.sqrt((price_delta**2 * time_delta + std**2 * (k_period-time_delta))/k_period)
        # print(std)
        price += price_delta
        time += time_delta

    # normalize prices 
    prices = np.array(prices)
    # lowest price = $1
    prices = prices - np.min(prices) + 1
    
    timestamps = np.array(timestamps)
        
    return prices, timestamps

def class_to_json(obj, classkey=None):
    if isinstance(obj, dict):
        data = {}
        for (k, v) in obj.items():
            data[k] = class_to_json(v, classkey)
        return data
    elif hasattr(obj, "_asdict"):
        return class_to_json(obj._asdict())
    elif hasattr(obj, "_ast"):
        return class_to_json(obj._ast())
    elif hasattr(obj, "__iter__"):
        return [class_to_json(v, classkey) for v in obj]
    elif hasattr(obj, "__dict__"):
        data = dict([(key, class_to_json(value, classkey))
                     for key, value in obj.__dict__.items()
                     if not callable(value) and not key.startswith('_')])
        if classkey is not None and hasattr(obj, "__class__"):
            data[classkey] = obj.__class__.__name__
        return data
    else:
        return obj


def close_all_users(clearing_house, verbose=False):
    clearing_houses = []
    events = []
    mark_prices = []
        
    # close out all the users 
    for market_index in range(len(clearing_house.markets)):
        market: Market = clearing_house.markets[market_index]
        
        for user_index in clearing_house.users:
            user: User = clearing_house.users[user_index]
            lp_position: MarketPosition = user.positions[market_index]
            is_lp = lp_position.lp_tokens > 0
            
            if is_lp: 
                if verbose: 
                    print(f'u{user_index} rl...')
                
                event = removeLiquidityEvent(
                    clearing_house.time, 
                    market_index, 
                    user_index,
                    lp_position.lp_tokens
                )
                clearing_house = event.run(clearing_house)
                
                mark_prices.append(calculate_mark_price(market))
                events.append(event)
                clearing_houses.append(copy.deepcopy(clearing_house))
            
                clearing_house = clearing_house.change_time(1)
            
            user: User = clearing_house.users[user_index]
            market_position: MarketPosition = user.positions[market_index]
            if market_position.base_asset_amount != 0: 
                if verbose: 
                    print(f'u{user_index} cp...')

                event = ClosePositionEvent(
                    clearing_house.time, 
                    user_index, 
                    market_index
                )
                clearing_house = event.run(clearing_house)
                
                mark_prices.append(calculate_mark_price(market))
                events.append(event)
                clearing_houses.append(copy.deepcopy(clearing_house))
                
                clearing_house = clearing_house.change_time(1)

    return clearing_house, (clearing_houses, events, mark_prices)

def compute_total_collateral(ch):
    init_collaterals = {}
    total_collateral = 0 
    for (i, user) in ch.users.items():
        init_collaterals[i] = user.collateral
        total_collateral += user.collateral
    # user_collateral = total_collateral
    # print('user collateral:', total_collateral/1e6)
    
    for market_index in range(len(ch.markets)):
        market: Market = ch.markets[market_index]
        total_collateral += market.amm.total_fee_minus_distributions
        # subtract what we paid lps for 
        total_collateral -= market.amm.lp_fee_payment
    # print('market collateral:', (total_collateral - user_collateral)/1e6)
    # print('total collateral:', total_collateral/1e6)

    total_collateral /= 1e6
    return total_collateral
