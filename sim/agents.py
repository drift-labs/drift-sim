from multiprocessing import Event
from driftpy.math.amm import calculate_amm_reserves_after_swap, get_swap_direction
from driftpy.math.amm import calculate_swap_output, calculate_terminal_price, calculate_mark_price_amm
from driftpy.math.trade import calculate_trade_slippage, calculate_target_price_trade, calculate_trade_acquired_amounts
from driftpy.math.positions import calculate_base_asset_value, calculate_position_pnl
from driftpy.types import PositionDirection, AssetType, MarketPosition
from driftpy.math.market import calculate_mark_price, calculate_bid_ask_price
from driftpy.constants.numeric_constants import AMM_TIMES_PEG_TO_QUOTE_PRECISION_RATIO, MARK_PRICE_PRECISION, PEG_PRECISION, QUOTE_PRECISION

from solana.publickey import PublicKey
import copy

import pandas as pd
import numpy as np

from programs.clearing_house.state import Oracle, User
from programs.clearing_house.lib import ClearingHouse
from sim.events import *
from programs.clearing_house.state import User, LPPosition

''' Agents ABC '''

class Agent:
    def __init__(self):
        ''' define params of agent '''
        pass

    def run(self, state_i: ClearingHouse) -> Event:
        ''' returns an event '''
        pass
    
    def setup(self, state_i: ClearingHouse) -> Event: 
        ''' called once at the start of the simulation '''
        pass
    
def default_user_deposit(
    user_index: int, 
    clearing_house: ClearingHouse,
    deposit_amount:int = 10_000_000,
) -> Event:
    event = DepositCollateralEvent(
        user_index=user_index, 
        deposit_amount=deposit_amount * QUOTE_PRECISION, # $10M
        timestamp=clearing_house.time, 
    )
    return event

class LP(Agent):
    def __init__(
        self, 
        lp_start_time: int = 0, 
        lp_duration: int = -1, 
        deposit_amount: int = 100 * QUOTE_PRECISION, 
        user_index: int = 0,
        market_index: int = 0,
    ) -> None:
        self.lp_start_time = lp_start_time
        # -1 means perma lp 
        self.lp_duration = lp_duration
        self.deposit_amount = deposit_amount
        
        self.user_index = user_index
        self.market_index = market_index 
        
        self.has_deposited = False 
        self.deposit_start = None
    
    def run(self, state_i: ClearingHouse) -> Event:
        now = state_i.time
        
        if not self.has_deposited: 
            self.deposit_start = now
            self.has_deposited = True 
            return addLiquidityEvent(
                timestamp=now, 
                market_index=self.market_index, 
                user_index=self.user_index, 
                quote_amount=self.deposit_amount
            )

        if self.lp_duration > 0 and now - self.deposit_start == self.lp_duration:
            user: User = state_i.users[self.user_index]
            lp_position: LPPosition = user.lp_positions[self.market_index]
            return removeLiquidityEvent(
                now, 
                self.market_index, 
                self.user_index, 
                lp_position.lp_tokens # full burn 
            )
        
        return NullEvent(now)
        

class Arb(Agent):
    ''' arbitrage a single market to oracle'''
    def __init__(
        self, 
        intensity: float, 
        market_index: int, 
        user_index: int, 
        lookahead:int = 0
    ):
        # assert(intensity > 0 and intensity <= 1)
        self.user_index = user_index
        self.market_index = market_index
        self.intensity = intensity
        self.lookahead = lookahead # default to looking at oracle at 0
        
    def setup(self, state_i: ClearingHouse) -> Event: 
        event = default_user_deposit(self.user_index, state_i)
        return event
        
    def run(self, state_i: ClearingHouse) -> Event:
        market_index = self.market_index
        user_index = self.user_index
        intensity = self.intensity

        now = state_i.time                                                             
        market = state_i.markets[market_index]
        oracle: Oracle = market.amm.oracle
        oracle_price = oracle.get_price(now)

        cur_mark = calculate_mark_price(market, oracle_price)
        target_mark = oracle.get_price(now + self.lookahead)
        target_mark = (target_mark - cur_mark) * intensity + cur_mark # only arb 1% of gap?
        # print(now, market.amm.peg_multiplier, calculate_mark_price_amm(market.amm), cur_mark, target_mark)

        # print(cur_mark, target_mark)

        #account for exchange fee in arb price
        exchange_fee = float(state_i.fee_structure.numerator)/state_i.fee_structure.denominator
        # print(exchange_fee)
        if target_mark < cur_mark*(1+exchange_fee) and target_mark > cur_mark*(1-exchange_fee):
            target_mark = cur_mark
        elif target_mark > cur_mark:
            target_mark = target_mark * (1-exchange_fee)
            # print('long to', target_mark, 'vs', cur_mark)
        elif target_mark < cur_mark:
            target_mark = target_mark * (1+exchange_fee)
            # print('short to', target_mark, 'vs', cur_mark)
        else:
            target_mark = cur_mark
        
        unit = AssetType.QUOTE

        direction, trade_size, entry_price, target_price = \
            calculate_target_price_trade(
                market, 
                int(target_mark * MARK_PRICE_PRECISION), 
                unit, 
                use_spread=True,
                oracle_price=oracle_price
            )
        
        trade_size = int(abs(trade_size)) # whole numbers only 
        if trade_size:
            print('NOW: ', now)
        quote_asset_reserve = (
            trade_size 
            * AMM_TIMES_PEG_TO_QUOTE_PRECISION_RATIO 
            / market.amm.peg_multiplier
        )
        
        # TODO: add this check to the clearing house 
        # convert to reserve amount 
        # trade size too small = no trade 
        if quote_asset_reserve < market.amm.minimum_quote_asset_trade_size: 
            trade_size = 0 
        
        if direction == PositionDirection.LONG:
            direction = 'long'
        else:
            direction = 'short'

        # arb is from 0 - x (intensity)
        # if trade_size != 0 and entry_price != 0:
        #     trade_size = max(self.intensity*100, 
        #                         min(trade_size*entry_price/(1e13), self.intensity*10000)
        #                         )/(entry_price) * 1e13
        
        if trade_size == 0:
            event = NullEvent(timestamp=now)
        else: 
            event = OpenPositionEvent(now, self.user_index, direction, int(trade_size), market_index)
            print(direction, trade_size/1e6, 'LUNA-PERP @', entry_price, '(',target_price/1e10,')')


        # print(now, market.amm.peg_multiplier, calculate_mark_price_amm(market.amm), cur_mark, target_mark)

        return event

class Noise(Agent):
    def __init__(self, intensity: float, market_index: int, user_index: int, lookahead:int = 0, size:int=1):
        # assert(intensity > 0 and intensity <= 1)
        self.intensity = intensity
        self.user_index = user_index
        self.market_index = market_index
        self.lookahead = lookahead # default to looking at oracle at 0 
        self.size = size
        
    def setup(self, state_i: ClearingHouse) -> Event: 
        event = default_user_deposit(self.user_index, state_i)
        return event

    def run(self, state_i: ClearingHouse) -> Event:
        market_index = self.market_index
        user_index = self.user_index
        intensity = self.intensity  
        direction = 'long'
        trade_size = int(self.size * 1e6)
        now = state_i.time   

        x = 5
        every_x_minutes = 60 * x
        if (now % every_x_minutes) < every_x_minutes - 1:
            return NullEvent(timestamp=now)                                                          

        event = OpenPositionEvent(now, self.user_index, direction, trade_size, market_index)
        return event

class ArbFunding(Agent):
    ''' arbitrage a single market to oracle'''
    def __init__(self, intensity: float, market_index: int, user_index: int, lookahead:int = 0):
        # assert(intensity > 0 and intensity <= 1)
        self.user_index = user_index
        self.intensity = intensity
        self.market_index = market_index
        self.lookahead = lookahead # default to looking at oracle at 0
        
    def setup(self, state_i: ClearingHouse) -> Event: 
        event = default_user_deposit(self.user_index, state_i)
        return event
        
    def run(self, state_i: ClearingHouse) -> Event:
        market_index = self.market_index
        user_index = self.user_index
        intensity = self.intensity

        now = state_i.time   

        market = state_i.markets[market_index]
        oracle: Oracle = market.amm.oracle
        oracle_price = oracle.get_price(now)

        if market.amm.funding_period - (now % 3600) > 100:
            return NullEvent(timestamp=now)

        bid, ask = calculate_bid_ask_price(market, oracle_price)

        funding_dollar = (market.amm.last_bid_price_twap + market.amm.last_ask_price_twap)/2 - market.amm.last_oracle_price_twap
        funding_dollar /= 24
        if funding_dollar > 0:
            slippage = funding_dollar/(oracle_price-bid)
            target = bid*(1-.0001)
        else:
            slippage = funding_dollar/(ask-oracle_price)
            target = ask*1.0001

        unit = AssetType.QUOTE
        direction, trade_size, entry_price, target_price = \
            calculate_target_price_trade(
                market, 
                int(target * MARK_PRICE_PRECISION), 
                unit, 
                use_spread=True,
                oracle_price=oracle_price
            )
        
        trade_size = min(10*1e6, int(abs(trade_size))) # whole numbers only 
        if trade_size:
            print('NOW: ', now)
        quote_asset_reserve = (
            trade_size 
            * AMM_TIMES_PEG_TO_QUOTE_PRECISION_RATIO 
            / market.amm.peg_multiplier
        )
        
        # TODO: add this check to the clearing house 
        # convert to reserve amount 
        # trade size too small = no trade 
        if quote_asset_reserve < market.amm.minimum_quote_asset_trade_size: 
            trade_size = 0 
        
        if direction == PositionDirection.LONG:
            direction = 'long'
        else:
            direction = 'short'

        # arb is from 0 - x (intensity)
        # if trade_size != 0 and entry_price != 0:
        #     trade_size = max(self.intensity*100, 
        #                         min(trade_size*entry_price/(1e13), self.intensity*10000)
        #                         )/(entry_price) * 1e13
        
        if trade_size == 0:
            event = NullEvent(timestamp=now)
        else: 
            event = OpenPositionEvent(now, self.user_index, direction, int(trade_size), market_index)
            print(direction, trade_size/1e6, 'LUNA-PERP @', entry_price, '(',target_price/1e10,')')


        # print(now, market.amm.peg_multiplier, calculate_mark_price_amm(market.amm), cur_mark, target_mark)

        return event
