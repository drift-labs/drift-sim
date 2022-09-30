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

from programs.clearing_house.state.market import SimulationMarket
from programs.clearing_house.state.user import MarketPosition

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
    clearing_house.time += 1e13 # to settle all the funding

    # close out all the users 
    for market_index in range(len(clearing_house.markets)):
        market: SimulationMarket = clearing_house.markets[market_index]
        clearing_house.update_funding_rate(market_index)
        
        for user_index in clearing_house.users:
            user: User = clearing_house.users[user_index]
            lp_position: MarketPosition = user.positions[market_index]
            is_lp = lp_position.lp_shares > 0
            
            if is_lp: 
                if verbose: 
                    print(f'u{user_index} rl...')
                
                event = removeLiquidityEvent(
                    timestamp=clearing_house.time, 
                    market_index=market_index, 
                    user_index=user_index,
                    lp_token_amount=-1
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
    
    for market_index in range(len(ch.markets)):
        market: SimulationMarket = ch.markets[market_index]
        total_collateral += market.amm.total_fee_minus_distributions 
        # total_collateral += market.amm.upnl # todo - amm.base/quote positon
        # total_collateral += market.amm.lp_funding_payment

    total_collateral /= 1e6
    return total_collateral

class RandomSimulation():
    def __init__(self, ch: ClearingHouse) -> None:
        self.ch = ch 
        market = ch.markets[0]
        self.max_t = len(market.amm.oracle)
        self.amm_tokens = market.amm.amm_lp_shares

    def generate_random_lp(self, user_index, market_index) -> Agent:
        
        import random
        token_amount = random.randint(0, self.amm_tokens)
        n_mints = np.random.randint(0, self.max_t//4)
        n_burns = np.random.randint(0, self.max_t//4)

        agent = RandomLP(
            token_amount=token_amount,
            n_mints=n_mints,
            n_burns=n_burns,
            user_index=user_index,
            market_index=market_index,
            max_t=self.max_t, 
        )
        return agent

    def generate_lp_settler(self, user_index, market_index, update_every=-1) -> Agent:
        if update_every == -1:
            update_every = np.random.randint(1, self.max_t // 2)

        return SettleLP(
            user_index, 
            market_index, 
            every_x_steps=update_every, 
        )

    def generate_lp(self, user_index, market_index) -> Agent:
        start = np.random.randint(0, self.max_t)
        dur = np.random.randint(0, self.max_t // 2)

        import random
        token_amount = random.randint(0, self.amm_tokens)

        return LP(
            lp_start_time=start,
            lp_duration=dur, 
            token_amount=token_amount, 
            user_index=user_index, 
            market_index=market_index, 
        )
    
    def generate_leveraged_trade(self, user_index, market_index, leverage) -> Agent:
        start = np.random.randint(0, self.max_t)
        dur = np.random.randint(0, self.max_t // 2)
        amount = np.random.randint(0, 100_000)
        quote_amount = amount * QUOTE_PRECISION
        
        return OpenClose(
            start_time=start,
            duration=dur, 
            direction='long' if np.random.choice([0, 1]) == 0 else 'short',
            quote_amount=quote_amount, 
            deposit_amount=quote_amount//leverage,
            user_index=user_index, 
            market_index=market_index
        )

    def generate_trade(self, user_index, market_index) -> Agent:
        start = np.random.randint(0, self.max_t)
        dur = np.random.randint(0, self.max_t // 2)
        amount = np.random.randint(0, 100_000)
        
        return OpenClose(
            start_time=start,
            duration=dur, 
            direction='long' if np.random.choice([0, 1]) == 0 else 'short',
            quote_amount=amount * QUOTE_PRECISION, 
            user_index=user_index, 
            market_index=market_index
        )

def collateral_difference(ch, initial_collateral, verbose=False):
    clearing_house = copy.deepcopy(ch)

    # close everyone 
    clearing_house, (chs, events, mark_prices) = close_all_users(clearing_house, verbose)
    
    # recompute collateral 
    end_total_collateral = compute_total_collateral(clearing_house)

    # ensure collateral still adds up 
    difference = initial_collateral - end_total_collateral
    abs_difference = abs(difference) 
    
    return (abs_difference, difference), events, chs, mark_prices
# %%
