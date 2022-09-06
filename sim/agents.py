from typing import Set
from driftpy.math.amm import calculate_amm_reserves_after_swap, get_swap_direction
from driftpy.math.amm import calculate_swap_output, calculate_terminal_price, calculate_mark_price_amm
from driftpy.math.trade import calculate_trade_slippage, calculate_target_price_trade, calculate_trade_acquired_amounts
from driftpy.math.positions import calculate_base_asset_value, calculate_position_pnl
from driftpy.types import PositionDirection, MarketPosition
from driftpy.math.market import calculate_mark_price, calculate_bid_ask_price
from driftpy.constants.numeric_constants import AMM_TIMES_PEG_TO_QUOTE_PRECISION_RATIO, MARK_PRICE_PRECISION, PEG_PRECISION, QUOTE_PRECISION
from driftpy._types import AssetType

from solana.publickey import PublicKey
import copy

import pandas as pd
import numpy as np

from programs.clearing_house.state import Oracle, User, user
from programs.clearing_house.lib import ClearingHouse
from sim.events import *
from programs.clearing_house.state import User 

''' Agents ABC '''

class Agent:
    def __init__(self):
        ''' define params of agent '''
        pass

    def run(self, state_i: ClearingHouse) -> [Event]:
        ''' returns an event '''
        pass
    
    def setup(self, state_i: ClearingHouse) -> [Event]: 
        ''' called once at the start of the simulation '''
        pass
    
def default_user_deposit(
    user_index: int, 
    clearing_house: ClearingHouse,
    deposit_amount:int = 10_000_000 * QUOTE_PRECISION,
    username: str = "u",
) -> [Event]:
    event = DepositCollateralEvent(
        user_index=user_index, 
        deposit_amount=deposit_amount, # $10M
        timestamp=clearing_house.time, 
        username=username
    )
    return event

class OpenClose(Agent):
    def __init__(
        self, 
        start_time: int = 0, 
        duration: int = -1, 
        quote_amount: int = 100 * QUOTE_PRECISION, 
        direction: str = 'long',
        user_index: int = 0,
        market_index: int = 0,
    ):
        self.start_time = start_time
        self.duration = duration
        self.direction = direction
        self.quote_amount = quote_amount
        self.user_index = user_index
        self.market_index = market_index
        self.has_opened = False
        self.deposit_start = None
        
    def setup(self, state_i: ClearingHouse) -> [Event]: 
        event = default_user_deposit(
            self.user_index, 
            state_i, 
            username='openclose', 
            deposit_amount=self.quote_amount
        )
        event = [event]
        return event

    def run(self, state_i: ClearingHouse) -> [Event]:
        now = state_i.time
        
        if (now == self.start_time) or (now > self.start_time and not self.has_opened): 
            self.deposit_start = now
            self.has_opened = True
            # print(f'u{self.user_index} op...')
            event = OpenPositionEvent(
                timestamp=now, 
                direction=self.direction,
                market_index=self.market_index, 
                user_index=self.user_index, 
                quote_amount=self.quote_amount
            )

        elif self.has_opened and self.duration > 0 and now - self.deposit_start == self.duration:
            # print(f'u{self.user_index} cp...')
            event = ClosePositionEvent(
                timestamp=now, 
                market_index=self.market_index, 
                user_index=self.user_index, 
            )
        else: 
            event = NullEvent(now)

        event = [event]
        return event
       

class RandomLP(Agent):
    def __init__(
        self,
        token_amount: int = 0,
        n_mints: int = 0,
        n_burns: int = 0,
        user_index: int = 0,
        market_index: int = 0,
        max_t: int = 0, # max time in the simulation
    ):
        self.n_mints = n_mints
        self.n_burns = n_burns
        self.user_index = user_index
        self.max_t = max_t

        self.user_index = user_index
        self.market_index = market_index

        import random
        self.mint_times = np.random.randint(0, self.max_t, size=(self.n_mints,))
        self.mint_amounts = [random.randint(0, token_amount) for _ in range(len(self.mint_times))]
        self.mint_index = 0 

        self.burn_times = np.random.randint(0, self.max_t, size=(self.n_burns,))
        self.burn_amounts = [random.randint(0, token_amount) for _ in range(len(self.mint_times))]
        self.burn_index = 0

    def setup(self, state_i: ClearingHouse) -> [Event]:
        # deposit amount which will be used as LP
        event = default_user_deposit(
            self.user_index,
            state_i,
            username='rando_LP',
        )
        event = [event]
        return event

    def run(self, state_i: ClearingHouse) -> [Event]:
        now = state_i.time 
        events = []

        if state_i.time in self.mint_times:
            if self.mint_index != len(self.mint_amounts) - 1:
                event = addLiquidityEvent(
                    timestamp=now, 
                    market_index=self.market_index, 
                    user_index=self.user_index, 
                    token_amount=self.mint_amounts[self.mint_index]
                )
                self.mint_index += 1 
                events.append(event)

        if state_i.time in self.burn_times: 
            if self.burn_index != len(self.burn_amounts) - 1:
                lp_shares = state_i.users[self.user_index].positions[self.market_index].lp_shares
                burn_amount = self.burn_amounts[self.burn_index]
                burn_amount = min(lp_shares, burn_amount) 

                event = removeLiquidityEvent(
                    timestamp=now, 
                    market_index=self.market_index, 
                    user_index=self.user_index, 
                    lp_token_amount=burn_amount
                ) 
                self.burn_index += 1 
                events.append(event)

        return events


class LP(Agent):
    def __init__(
        self, 
        lp_start_time: int = 0, 
        lp_duration: int = -1, 
        token_amount: int = 100 * 1e13, 
        user_index: int = 0,
        market_index: int = 0,
    ) -> None:
        self.lp_start_time = lp_start_time
        # -1 means perma lp 
        self.lp_duration = lp_duration
        self.token_amount = token_amount
        
        self.user_index = user_index
        self.market_index = market_index 
        
        self.has_deposited = False 
        self.deposit_start = None
        
    def setup(self, state_i: ClearingHouse) -> [Event]: 
        # deposit amount which will be used as LP 
        event = default_user_deposit(
            self.user_index,
            state_i,
            username='LP',
        )
        
        # # TODO: update this to meet margin requirements
        # event = NullEvent(state_i.time)
        
        event = [event]
        return event
    
    def run(self, state_i: ClearingHouse) -> [Event]:
        now = state_i.time
        
        if (now == self.lp_start_time) or (now > self.lp_start_time and not self.has_deposited): 
            self.deposit_start = now
            self.has_deposited = True 
            # print(f'u{self.user_index} al..')
            event = addLiquidityEvent(
                timestamp=now, 
                market_index=self.market_index, 
                user_index=self.user_index, 
                token_amount=self.token_amount
            )

        elif self.has_deposited and self.lp_duration > 0 and now - self.deposit_start == self.lp_duration:
            user: User = state_i.users[self.user_index]
            # print(f'u{self.user_index} rl..')
            event = removeLiquidityEvent(
                timestamp=now, 
                market_index=self.market_index, 
                user_index=self.user_index, 
                lp_token_amount=self.token_amount
            ) # full burn 
        else: 
            event = NullEvent(now)

        event = [event]
        return event

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
        
    def setup(self, state_i: ClearingHouse) -> [Event]: 
        event = default_user_deposit(self.user_index, state_i, username='arb')
        event = [event]
        return event
        
    def run(self, state_i: ClearingHouse) -> [Event]:
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
        # if trade_size:
        #     print('NOW: ', now)
        #     print("direction, trade_size, entry_price, target_price:", direction, trade_size, entry_price, target_price)
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
            # print(direction, trade_size/1e6, 'LUNA-PERP @', entry_price, '(',target_price/1e10,')')


        event = [event]
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
        
    def setup(self, state_i: ClearingHouse) -> [Event]: 
        event = default_user_deposit(self.user_index, state_i, username='noise')
        event = [event]
        return event

    def run(self, state_i: ClearingHouse) -> [Event]:
        market_index = self.market_index
        user_index = self.user_index
        intensity = self.intensity  
        direction = 'long'
        trade_size = int(self.size * 1e6)
        now = state_i.time   

        x = 5
        every_x_minutes = 60 * x
        if (now % every_x_minutes) < every_x_minutes - 1:
            event = NullEvent(timestamp=now)
            event = [event]

            return event

        event = OpenPositionEvent(now, self.user_index, direction, trade_size, market_index)
        event = [event]
        return event

class SettleLP(Agent):
    def __init__(self, user_index: int, market_index: int, every_x_steps: int = 1) -> None:
        self.user_index = user_index
        self.market_index = market_index
        self.every_x_steps = every_x_steps

    def setup(self, state: ClearingHouse) -> [Event]:
        event = NullEvent(state.time)
        event = [event]
        return event

    def run(self, state: ClearingHouse) -> [Event]: 
        event = NullEvent(state.time)
        if state.time % self.every_x_steps == 0: 
            if state.users[self.user_index].positions[self.market_index].lp_shares != 0:
                # only settle if/when they are an lp 
                event = SettleLPEvent(
                    timestamp=state.time, 
                    user_index=self.user_index, 
                    market_index=self.market_index,
                )
            else: 
                event = NullEvent(state.time)

        event = [event]
        return event

class ArbFunding(Agent):
    ''' arbitrage a single market to oracle'''
    def __init__(self, intensity: float, market_index: int, user_index: int, lookahead:int = 0):
        # assert(intensity > 0 and intensity <= 1)
        self.user_index = user_index
        self.intensity = intensity
        self.market_index = market_index
        self.lookahead = lookahead # default to looking at oracle at 0
        
    def setup(self, state_i: ClearingHouse) -> [Event]: 
        event = default_user_deposit(self.user_index, state_i, username='arbfund',)
        event = [event]
        return event
        
    def run(self, state_i: ClearingHouse) -> [Event]:
        market_index = self.market_index
        user_index = self.user_index
        intensity = self.intensity

        now = state_i.time   

        market = state_i.markets[market_index]
        oracle: Oracle = market.amm.oracle
        oracle_price = oracle.get_price(now)

        if market.amm.funding_period - (now % 3600) > 100:
            event = NullEvent(timestamp=now)
            event = [event]
            return event

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
            print('agent: trade size not large enough...')
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
            print(direction, trade_size/1e6, 'LUNA-PERP @', entry_price, '(',target_price/1e10,')', f"ts:{now}")


        event = [event]
        # print(now, market.amm.peg_multiplier, calculate_mark_price_amm(market.amm), cur_mark, target_mark)

        return event
