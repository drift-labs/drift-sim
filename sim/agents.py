from typing import Set
from driftpy.math.amm import calculate_amm_reserves_after_swap, get_swap_direction
from driftpy.math.amm import calculate_swap_output, calculate_terminal_price, calculate_mark_price_amm
from driftpy.math.trade import calculate_trade_slippage, calculate_target_price_trade, calculate_trade_acquired_amounts
from driftpy.math.positions import calculate_base_asset_value, calculate_position_pnl
from driftpy.types import PositionDirection, PerpPosition
from driftpy.math.market import calculate_mark_price, calculate_bid_ask_price
from driftpy.constants.numeric_constants import AMM_TIMES_PEG_TO_QUOTE_PRECISION_RATIO, PRICE_PRECISION as PRICE_PRECISION, PEG_PRECISION, QUOTE_PRECISION
from driftpy._types import AssetType

from solana.publickey import PublicKey
import copy

import pandas as pd
import numpy as np

from sim.driftsim.clearing_house.state import Oracle, User, user
from sim.driftsim.clearing_house.lib import ClearingHouse
from sim.events import *
from sim.driftsim.clearing_house.state import User 

''' Agents ABC '''

class Agent:
    def __init__(self):
        ''' define params of agent '''
        pass

    def run(self, state_i: ClearingHouse) -> list[Event]:
        ''' returns an event '''
        pass
    
    def setup(self, state_i: ClearingHouse) -> list[Event]: 
        ''' called once at the start of the simulation '''
        pass
    
def default_user_deposit(
    user_index: int, 
    clearing_house: ClearingHouse,
    deposit_amount:int = 100_000 * QUOTE_PRECISION,
    spot_market_index=0,
    username: str = "u",
) -> DepositCollateralEvent:
    event = DepositCollateralEvent(
        user_index=user_index, 
        deposit_amount=deposit_amount, # $10M
        timestamp=clearing_house.time, 
        spot_market_index=spot_market_index,
        username=username
    )
    return event

class MultipleAgent(Agent):
    def __init__(
        self, 
        subagent_init_fcn,
        n_subagents, 
    ):
        self.subagents = []
        for _ in range(n_subagents):
            self.subagents.append(
                subagent_init_fcn()
            )

        self.user_index = self.subagents[0].user_index
        self.deposit_amount = sum([agent.deposit_amount for agent in self.subagents])

    def setup(self, state_i: ClearingHouse) -> list[Event]: 
        event = default_user_deposit(
            self.user_index, 
            state_i, 
            username=f'multiple-{self.subagents[0].name}', 
            deposit_amount=self.deposit_amount
        )
        event = [event]
        return event

    def run(self, state_i: ClearingHouse) -> list[Event]:
        events = []
        for agent in self.subagents:
            events += agent.run(state_i)
        
        return events

@dataclass
class Borrower(Agent):
    asset_spot_index: int 
    liability_spot_index: int 
    deposit_amount: int 
    borrow_amount: int
    user_index: int

    start_time: int = 0
    duration: int = -1 
    name: str = 'borrower'
    has_opened: bool = False

    @staticmethod
    def random_init(max_t, n_spot_markets, user_index): 
        start = np.random.randint(0, max_t - 2)
        dur = np.random.randint(0, max_t - start - 1)

        deposit_amount = np.random.randint(0, QUOTE_PRECISION * 100_000)
        borrow_amount = np.random.randint(0, deposit_amount)

        all_spot_markets = list(range(n_spot_markets))
        # sample two idxs => one for asset/liability 
        asset, liab = np.random.choice(all_spot_markets, size=(2,), replace=False)
        asset, liab = int(asset), int(liab)

        return Borrower(
            asset, 
            liab, 
            deposit_amount, 
            borrow_amount, 
            user_index=user_index,
            start_time=start,
            duration=dur,
        )
    
    def setup(self, state_i: ClearingHouse) -> list[Event]: 
        if self.deposit_amount > 0:
            event = default_user_deposit(
                self.user_index, 
                state_i, 
                username=self.name, 
                deposit_amount=self.deposit_amount,
                spot_market_index=self.asset_spot_index
            )
            event = [event]
        else: 
            event = []
        return event

    def run(self, state_i: ClearingHouse) -> list[Event]:
        now = state_i.time
        events = []
        
        if (now == self.start_time) or (now > self.start_time and not self.has_opened): 
            self.deposit_start = now
            self.has_opened = True

            # compute price of both asset and liab 
            if self.asset_spot_index == 0:
                asset_price = 1
            else:
                asset_price = state_i.spot_markets[self.asset_spot_index-1].oracle.get_price(now)

            if self.liability_spot_index == 0:
                liab_price = 1
            else:
                liab_price = state_i.spot_markets[self.liability_spot_index-1].oracle.get_price(now)
            
            total_collateral = self.deposit_amount * asset_price
            liability_price = self.borrow_amount * liab_price

            # add more so we can withdraw
            if liability_price > total_collateral: 
                event = MidSimDepositEvent(
                    timestamp=now, 
                    user_index=self.user_index, 
                    spot_market_index=self.asset_spot_index, 
                    deposit_amount=(liability_price - total_collateral), 
                    reduce_only=False
                )
                events.append(event)

            event = WithdrawEvent(
                timestamp=now, 
                user_index=self.user_index, 
                spot_market_index=self.liability_spot_index, 
                withdraw_amount=self.borrow_amount, 
                reduce_only=False,
            )
        elif self.has_opened and self.duration > 0 and now - self.deposit_start == self.duration:
            event = MidSimDepositEvent(
                timestamp=now, 
                user_index=self.user_index, 
                spot_market_index=self.liability_spot_index, 
                deposit_amount=self.borrow_amount, 
                reduce_only=True
            )
        else: 
            event = NullEvent(now)
        
        events.append(event)
        return events


@dataclass
class IFStaker(Agent):
    stake_amount: int
    spot_market_index: int
    user_index: int
    start_time: int = 0
    duration: int = -1
    name: str = 'if_staker'
    has_opened: bool = False

    @staticmethod
    def random_init(max_t, user_index, spot_market_index): 
        start = np.random.randint(0, max_t - 2)
        dur = np.random.randint(0, max_t - start - 1)
        stake_amount = np.random.randint(0, QUOTE_PRECISION * 100)

        return IFStaker(
            stake_amount, 
            spot_market_index, 
            user_index, 
            start_time=start,
            duration=dur,
        )

    def setup(self, state_i: ClearingHouse) -> list[Event]: 
        event = default_user_deposit(
            self.user_index, 
            state_i, 
            username=self.name, 
            deposit_amount=self.stake_amount,
            spot_market_index=self.spot_market_index
        )
        event.mint_amount = event.deposit_amount
        event.deposit_amount = 0

        s_event = InitIfStakeEvent(
            state_i.time, 
            self.user_index, 
            self.spot_market_index
        )
        event = [event, s_event]
        return event

    def run(self, state_i: ClearingHouse) -> list[Event]:
        now = state_i.time
        
        if (now == self.start_time) or (now > self.start_time and not self.has_opened): 
            self.deposit_start = now
            self.has_opened = True
            event = AddIfStakeEvent(
                timestamp=now, 
                user_index=self.user_index, 
                market_index=self.spot_market_index, 
                amount=self.stake_amount
            )
        elif self.has_opened and self.duration > 0 and now - self.deposit_start == self.duration:
            event = RemoveIfStakeEvent(
                timestamp=now, 
                user_index=self.user_index, 
                market_index=self.spot_market_index, 
                amount=-1
            )
        else: 
            event = NullEvent(now)

        return [event]

@dataclass
class Liquidator(Agent):
    user_index: int
    deposits: list[int] # spot market deposits
    every_t_times: int = 1
    name = 'liquidator'

    def setup(self, state_i: ClearingHouse) -> list[Event]: 
        events = []
        for i, deposit in enumerate(self.deposits):
            event = default_user_deposit(
                self.user_index, 
                state_i, 
                username=self.name, 
                deposit_amount=deposit,
                spot_market_index=i
            )
            events.append(event)
        return events

    def run(self, state_i: ClearingHouse):
        now = state_i.time
        if now % self.every_t_times == 0:
            return [LiquidateEvent(
                now, 
                self.user_index, 
            )]
        else: 
            return [NullEvent(now)]

class OpenClose(Agent):
    def __init__(
        self, 
        start_time: int = 0, 
        duration: int = -1, 
        quote_amount: int = 100 * QUOTE_PRECISION, 
        direction: str = 'long',
        user_index: int = 0,
        market_index: int = 0,
        deposit_amount: int = None
    ):
        self.start_time = start_time
        self.duration = duration
        self.direction = direction
        self.quote_amount = quote_amount
        self.user_index = user_index
        self.market_index = market_index
        self.has_opened = False
        self.deposit_start = None

        self.deposit_amount = deposit_amount
        if deposit_amount is None: 
            self.deposit_amount = self.quote_amount

        self.name = 'openclose'

    @staticmethod
    def random_init(max_t, user_index, market_index, short_bias, leave_open_odds=0.5, leverage=1):
        assert short_bias <= 1 and short_bias >= 0, "invalid short bias value"
        assert leave_open_odds <= 1 and leave_open_odds >= 0, "invalid leave open odds value"
        
        start = np.random.randint(0, max_t - 2)
        dur = np.random.randint(0, max_t - start - 1)
        amount = np.random.randint(0, QUOTE_PRECISION * 100)
        quote_amount = amount 

        # dont close it ???
        should_leave_open = np.random.choice([1, 0], p=[leave_open_odds, 1-leave_open_odds])
        if should_leave_open:
            dur = max_t + 1
        
        return OpenClose(
            start_time=start,
            duration=dur, 
            direction='long' if np.random.choice([1, 0], p=[1 - short_bias, short_bias]) else 'short',
            quote_amount=quote_amount, 
            deposit_amount=quote_amount//leverage,
            user_index=user_index, 
            market_index=market_index
        )
        
    def setup(self, state_i: ClearingHouse) -> list[Event]: 
        event = default_user_deposit(
            self.user_index, 
            state_i, 
            username=self.name, 
            deposit_amount=self.deposit_amount
        )
        event = [event]
        return event

    def run(self, state_i: ClearingHouse) -> list[Event]:
        now = state_i.time
        
        if (now == self.start_time) or (now > self.start_time and not self.has_opened): 
            self.deposit_start = now
            self.has_opened = True
            market = state_i.markets[self.market_index]
            amount = min(self.quote_amount, market.amm.quote_asset_reserve)
            # print(f'u{self.user_index} op...')
            event = OpenPositionEvent(
                timestamp=now, 
                direction=self.direction,
                market_index=self.market_index, 
                user_index=self.user_index, 
                quote_amount=amount
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
       
class AddRemoveLiquidity(Agent):
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

        # TODO match margin req: 
        self.deposit_amount = 10_000_000 * QUOTE_PRECISION
        self.name = 'liquidity-provider'

    @staticmethod
    def random_init(max_t, user_index, market_index, min_token_amount=0, max_token_amount=100 * AMM_RESERVE_PRECISION, leverage=1):
        start = np.random.randint(0, max_t - 2)
        dur = np.random.randint(0, max_t - start - 1)
        token_amount = np.random.randint(min_token_amount, max_token_amount)

        return AddRemoveLiquidity(
            lp_start_time=start,
            lp_duration=dur, 
            token_amount=token_amount, 
            user_index=user_index, 
            market_index=market_index, 
        )
        
    def setup(self, state_i: ClearingHouse) -> list[Event]: 
        # deposit amount which will be used as LP 
        event = default_user_deposit(
            self.user_index,
            state_i,
            username='LP',
            deposit_amount=self.deposit_amount
        )
        
        # # TODO: update this to meet margin requirements
        # event = NullEvent(state_i.time)
        
        event = [event]
        return event
    
    def run(self, state_i: ClearingHouse) -> list[Event]:
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
        
    def setup(self, state_i: ClearingHouse) -> list[Event]: 
        event = default_user_deposit(self.user_index, state_i, username='arb')
        event = [event]
        return event
        
    def run(self, state_i: ClearingHouse) -> list[Event]:
        market_index = self.market_index
        user_index = self.user_index
        intensity = self.intensity

        now = state_i.time                                                             
        market = state_i.markets[market_index]
        oracle: Oracle = market.amm.oracle
        oracle_price = oracle.get_price(now)
        # print('ORACLE PRICE', oracle_price)

        cur_mark = calculate_mark_price(market, oracle_price)
        target_mark = oracle.get_price(now + self.lookahead)
        target_mark = (target_mark - cur_mark) * intensity + cur_mark # only arb 1% of gap?
        # print(now, market.amm.peg_multiplier, calculate_mark_price_amm(market.amm), cur_mark, target_mark)

        # print(cur_mark, target_mark)

        #account for exchange fee in arb price
        exchange_fee = float(state_i.fee_structure.numerator)/state_i.fee_structure.denominator

        # print(target_mark, exchange_fee)
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
        if target_mark > cur_mark:
            direction = PositionDirection.LONG
        else:
            direction = PositionDirection.SHORT
        # direction, trade_size, entry_price, target_price = \
        #     calculate_target_price_trade(
        #         market, 
        #         int(target_mark * PRICE_PRECISION), 
        #         unit, 
        #         use_spread=True,
        #         oracle_price=oracle_price
        #     )
        # print("direction, trade_size, entry_price, target_price:", direction, trade_size, entry_price, target_price)
        trade_size = int(abs(QUOTE_PRECISION * 10_000)) # whole numbers only 
        entry_price = (target_mark+cur_mark)/2
        # if trade_size:
            # print('NOW: ', now)
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
        if trade_size != 0 and entry_price != 0:
            trade_size = QUOTE_PRECISION
            # trade_size = max(self.intensity*100, 
            #                     min(trade_size*entry_price/(1e13), self.intensity)
            #                     )/(entry_price) * 1e13
        
        if trade_size == 0:
            event = NullEvent(timestamp=now)
        else: 
            # event = OpenPositionEvent(now, self.user_index, direction, int(trade_size), market_index)
            event = OpenPositionEvent(
                timestamp=now, 
                direction=direction,
                market_index=market_index, 
                user_index=self.user_index, 
                quote_amount=int(trade_size)
            )
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
        
    def setup(self, state_i: ClearingHouse) -> list[Event]: 
        event = default_user_deposit(self.user_index, state_i, username='noise')
        event = [event]
        return event

    def run(self, state_i: ClearingHouse) -> list[Event]:
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

class SettlePnL(Agent):
    def __init__(self, user_index: int, market_index: int, every_x_steps: int = 1, start: int = 0) -> None:
        self.user_index = user_index
        self.market_index = market_index
        self.every_x_steps = every_x_steps
        self.start = start

        self.name = 'settler_pnl'
        self.deposit_amount = 0

    @staticmethod
    def random_init(max_t, user_index, market_index, update_every=-1, start=-1):
        if update_every == -1:
            update_every = np.random.randint(1, max_t // 4)

        if start == -1:
            start = np.random.randint(1, max_t // 4)
        
        return SettlePnL(
            user_index, 
            market_index, 
            every_x_steps=update_every, 
            start=start,
        )

    def setup(self, state: ClearingHouse) -> list[Event]:
        event = NullEvent(state.time)
        event = [event]
        return event

    def run(self, state: ClearingHouse) -> list[Event]: 
        events = []
        if state.time % self.every_x_steps == 0 and state.time > self.start: 
            user: User = state.users[self.user_index]
            position = user.positions[self.market_index]

            # only settle if they have position 
            if position.base_asset_amount != 0:
                event = SettlePnLEvent(
                    timestamp=state.time, 
                    user_index=self.user_index, 
                    market_index=self.market_index,
                )
                events.append(event)

        return events

class SettleLP(Agent):
    def __init__(self, user_index: int, market_index: int, every_x_steps: int = 1) -> None:
        self.user_index = user_index
        self.market_index = market_index
        self.every_x_steps = every_x_steps

        self.name = 'settler_lp'
        self.deposit_amount = 0

    @staticmethod
    def random_init(max_t, user_index, market_index, update_every=-1):
        if update_every == -1:
            update_every = np.random.randint(1, max_t // 4)

        return SettleLP(
            user_index, 
            market_index, 
            every_x_steps=update_every, 
        )

    def setup(self, state: ClearingHouse) -> list[Event]:
        event = NullEvent(state.time)
        event = [event]
        return event

    def run(self, state: ClearingHouse) -> list[Event]: 
        events = []
        if state.time % self.every_x_steps == 0: 
            if state.users[self.user_index].positions[self.market_index].lp_shares != 0:
                # only settle if/when they are an lp 
                event = SettleLPEvent(
                    timestamp=state.time, 
                    user_index=self.user_index, 
                    market_index=self.market_index,
                )
                events.append(event)

        return events

class ArbFunding(Agent):
    ''' arbitrage a single market to oracle'''
    def __init__(self, intensity: float, market_index: int, user_index: int, lookahead:int = 0):
        # assert(intensity > 0 and intensity <= 1)
        self.user_index = user_index
        self.intensity = intensity
        self.market_index = market_index
        self.lookahead = lookahead # default to looking at oracle at 0
        
    def setup(self, state_i: ClearingHouse) -> list[Event]: 
        event = default_user_deposit(self.user_index, state_i, username='arbfund',)
        event = [event]
        return event
        
    def run(self, state_i: ClearingHouse) -> list[Event]:
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
                int(target * PRICE_PRECISION), 
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
