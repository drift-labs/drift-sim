#%%
import sys 
import driftpy
import copy 

from driftpy.math.amm import (
    calculate_swap_output, 
    calculate_amm_reserves_after_swap, 
    get_swap_direction, 
    calculate_price,
)
from driftpy.math.repeg import calculate_repeg_cost, calculate_budgeted_repeg
from driftpy.math.trade import calculate_trade_slippage, calculate_target_price_trade, calculate_trade_acquired_amounts
from driftpy.math.positions import calculate_base_asset_value, calculate_position_pnl, calculate_position_funding_pnl
from driftpy.types import PositionDirection, AssetType, MarketPosition, SwapDirection
from driftpy.math.market import calculate_mark_price, calculate_bid_price, calculate_ask_price,     calculate_freepeg_cost

from driftpy.math.amm import calculate_mark_price_amm, calculate_bid_price_amm, calculate_ask_price_amm, calculate_peg_multiplier
# from driftpy.math.repeg import calculate_freepeg_cost

from driftpy.math.user import *

from driftpy.constants.numeric_constants import * 
from programs.clearing_house.controller.amm import *

from solana.publickey import PublicKey

import json 
import matplotlib.pyplot as plt 
import numpy as np 
import pandas as pd
from dataclasses import dataclass, field

from programs.clearing_house.math.pnl import *
from programs.clearing_house.math.amm import *
from programs.clearing_house.state import *
from programs.clearing_house.state.user import User, MarketPosition, LPPosition

MARGIN_PRECISION = 10_000 # expo = -4

@dataclass
class ClearingHouse: 
    markets: list[Market]
    fee_structure: FeeStructure
    users: dict = field(default_factory=dict)
    time: int = 0 
    name: str = ''
    
    def __post_init__(self):
        for index, market in enumerate(self.markets):
            market.market_index = index
    
    def deposit_user_collateral(
        self,
        user_index, 
        collateral_amount
    ):
        # initialize user if not already 
        if user_index not in self.users: 
            market_positions = [MarketPosition() for _ in range(len(self.markets))]
            lp_positions = [LPPosition() for _ in range(len(self.markets))]
            self.users[user_index] = User(
                collateral=0, 
                positions=market_positions, 
                lp_positions=lp_positions
            )

        user = self.users[user_index]
        user.collateral += collateral_amount
        user.cumulative_deposits += collateral_amount
        
        return self 
    
    def add_liquidity(
        self, 
        market_index: int, 
        user_index: int, 
        quote_amount: int, 
    ):
        assert quote_amount > 0 
        
        user: User = self.users[user_index]
        
        market: Market = self.markets[market_index]
        assert market.amm.lp_tokens > 0, "No liquidity to add"
        assert user.positions[market_index].base_asset_amount == 0, "Close position before lping"
        assert user.collateral >= quote_amount, "Not enough collateral to add liquidity"
        
        # compute lp token amount for a given quote amount
        # amm: lptokens = 100, total_lp_value = 100 
        # user: deposits 50 value => 50 * [100 / 100] = 50 lp tokens 
        user_lp_token_amount = int(
            quote_amount * 
            market.amm.total_lp_tokens / 
            market.amm.total_lp_value
        )
        assert user_lp_token_amount <= market.amm.lp_tokens, "trying to add too much liquidity"
        
        # lock collateral 
        user.locked_collateral += quote_amount
        
        # record other metrics
        user_lp_position: LPPosition = LPPosition(
            market_index=market_index,
            lp_tokens=user_lp_token_amount,
            last_cumulative_lp_funding=market.amm.cumulative_lp_funding,
            last_net_position=market.amm.net_base_asset_amount, 
            last_fee_amount=market.amm.total_fee, # TODO: figure out the earmark shtuff
        )
        user.lp_positions[market_index] = user_lp_position
        
        # transfer position from amm => user 
        market.amm.lp_tokens -= user_lp_token_amount
        
        return self 
        
    def burn(
        self, 
        market_index: int, 
        user_index: int, 
        lp_token_amount: int, 
    ):
        user: User = self.users[user_index]
        market: Market = self.markets[market_index]
        lp_position: LPPosition = user.lp_positions[market_index]
        
        # unlock their total collateral 
        user.locked_collateral = 0 
        
        # give them portion of fees since deposit 
        total_lp_tokens = market.amm.total_lp_tokens
        change_in_fees = market.amm.total_fee - lp_position.last_fee_amount
        fee_amount = change_in_fees * lp_token_amount / total_lp_tokens  
        user.collateral += fee_amount
        market.amm.total_fee -= fee_amount
        
        # give them portion of funding since deposit
        # change_in_funding = market.amm.cumulative_lp_funding - lp_position.
        
        # give them the amm position  
        amm_net_position_change = (
            lp_position.last_net_position - 
            market.amm.net_base_asset_amount
        )
        
        if amm_net_position_change != 0: 
            base_position_amount = (
                amm_net_position_change
                * lp_token_amount 
                / total_lp_tokens
            )
            last_funding_rate = {
                True: market.amm.cumulative_funding_rate_long, 
                False: market.amm.cumulative_funding_rate_short, 
            }[base_position_amount > 0]
                
            new_position = MarketPosition(
                market_index=market_index,
                base_asset_amount=base_position_amount, 
                quote_asset_amount=0, # TODO - would this be the amount the user deposited? 
                last_cumulative_funding_rate=last_funding_rate,
                last_funding_rate_ts=self.time,
            )
            user.positions[market_index] = new_position
            
        return self 
        
    def change_time(self, time_delta):
        self.time = self.time + time_delta
        return self 
        
    def update_funding_rate(
        self, 
        market_index
    ): 
        now = self.time
        market = self.markets[market_index]
        
        last_funding_ts = market.amm.last_funding_rate_ts
        funding_period = market.amm.funding_period
        
        time_since_last_update = now - last_funding_ts
        next_update_wait = funding_period
        
        if funding_period > 1:
            last_update_delay = last_funding_ts % funding_period
            
            if last_update_delay != 0:
                max_delay_for_next_period = funding_period / 3
                two_funding_periods = funding_period * 2

                if last_update_delay > max_delay_for_next_period:
                    next_update_wait = two_funding_periods - last_update_delay
                else: 
                    next_update_wait = funding_period - last_update_delay
        
                if next_update_wait > two_funding_periods: 
                    next_update_wait = next_update_wait - funding_period
        
        if time_since_last_update >= next_update_wait:
            mark_twap = update_mark_twap(market.amm, now)
            oracle_twap = update_oracle_twap(market.amm, now)
            
            price_spread = mark_twap - oracle_twap
            
            max_price_spread = oracle_twap / 33 # 3% of oracle price
            clamped_price_spread = np.clip(price_spread, -max_price_spread, max_price_spread)
                    
            adjustment = 24 ## 24 slots of funding period time till full payback -- hardcode for now
            funding_rate = int(clamped_price_spread * FUNDING_PRECISION / adjustment)

            # TODO: cap funding rate if it's too high against the clearing house            
            # # market base asset amount * funding rate 
            # net_market_position_funding_payment = (
            #     market.net_base_asset_amount * funding_rate 
            #     / MARK_PRICE_PRECISION 
            #     / FUNDING_PRECISION
            #     / AMM_TO_QUOTE_PRECISION_RATIO
            # )
            # # market always pays opposite of the users 
            # uncapped_funding_pnl = -net_market_position_funding_payment
            
            market.amm.cumulative_funding_rate_long += funding_rate
            market.amm.cumulative_funding_rate_short += funding_rate
            
            market.amm.last_funding_rate = funding_rate
            market.amm.last_funding_rate_ts = now     
            
            # TODO: double check compute lp funding 
            market_net_pos = -market.amm.net_base_asset_amount
            
            # TODO: should these be different? 
            market_funding_rate = 0 
            if market_net_pos > 0: 
                market_funding_rate = funding_rate
            if market_net_pos < 0: 
                market_funding_rate = funding_rate
            
            market_funding_payment = (
                market_funding_rate 
                * market_net_pos
                / MARK_PRICE_PRECISION 
                / FUNDING_PRECISION
            )
            market.amm.cumulative_lp_funding += market_funding_payment
            
        return self
        
    def settle_funding_rates(
        self, 
        user_index
    ):
        now = self.time 
        user = self.users[user_index]
        total_funding_payment = 0 
        for i in range(len(self.markets)): 
            market: Market = self.markets[i]
            position: MarketPosition = user.positions[i]
            
            if position.base_asset_amount == 0: 
                continue
            
            amm_cumulative_funding_rate = {
                True: market.amm.cumulative_funding_rate_long, 
                False: market.amm.cumulative_funding_rate_short
            }[position.base_asset_amount > 0]
            
            if position.last_cumulative_funding_rate != amm_cumulative_funding_rate:
                funding_delta = amm_cumulative_funding_rate - position.last_cumulative_funding_rate

                funding_payment = (
                    funding_delta 
                    * position.base_asset_amount
                    / MARK_PRICE_PRECISION 
                    / FUNDING_PRECISION
                )
  
                # long @ f0 funding rate 
                # mark < oracle => funding_payment = mark - oracle < 0 => cum_funding decreases 
                # amm_cum < f0 [bc of decrease]
                # amm_cum - f0 < 0  :: long doesnt get paid in funding 
                # flip sign to make long get paid (not in v1 program? maybe doing something wrong)
                funding_payment = -funding_payment
                
                total_funding_payment += funding_payment
                position.last_cumulative_funding_rate = amm_cumulative_funding_rate
                position.last_funding_rate_ts = now 
        
        funding_payment_collateral = total_funding_payment / AMM_TO_QUOTE_PRECISION_RATIO
        user.collateral = calculate_updated_collateral(
            user.collateral, 
            funding_payment_collateral
        )
        return self

    def increase(
        self, 
        quote_amount: float, 
        direction: PositionDirection, 
        market_position: MarketPosition, 
        market: Market
    ):         
        # update the funding rate if new position 
        if market_position.base_asset_amount == 0:
            market_position.last_cumulative_funding_rate = {
                PositionDirection.LONG: market.amm.cumulative_funding_rate_long,
                PositionDirection.SHORT: market.amm.cumulative_funding_rate_short
            }[direction]
            market.open_interest += 1 
            
        market_position.quote_asset_amount += quote_amount
        
        # do swap 
        swap_direction = {
            PositionDirection.LONG: SwapDirection.ADD,
            PositionDirection.SHORT: SwapDirection.REMOVE
        }[direction]
        
        now = self.time
        base_amount_acquired, quote_asset_amount_surplus = swap_quote_asset(
            market.amm, 
            quote_amount, 
            swap_direction,
            now,
            market.amm.base_spread > 0
        )
        
        market_position.base_asset_amount += base_amount_acquired
        
        if base_amount_acquired > 0:
            market.base_asset_amount_long += base_amount_acquired
        else:
            market.base_asset_amount_short += base_amount_acquired 

        market.base_asset_amount += base_amount_acquired
        market.amm.net_base_asset_amount += base_amount_acquired
                
        return base_amount_acquired, quote_asset_amount_surplus

    def repeg(self, market: Market, new_peg: int):

        cost, mark_delta = calculate_repeg_cost(market, new_peg)
        # print('repeg cost:', cost)
        market.amm.peg_multiplier = new_peg

        # market.total_fees -= cost*1e6
        # market.total_mm_fees -= cost*1e6

        # market.amm.total_fee -= cost*1e6
        market.amm.total_fee_minus_distributions -= cost*1e6

    
    def reduce(
        self, 
        direction: PositionDirection, 
        quote_amount: float, 
        user: User, 
        market_position: MarketPosition, 
        market: Market
    ):         
        swap_direction = {
            PositionDirection.LONG: SwapDirection.ADD,
            PositionDirection.SHORT: SwapDirection.REMOVE
        }[direction]
        
        prev_base_amount = market_position.base_asset_amount
        
        now = self.time
        base_amount_acquired, quote_asset_amount_surplus = swap_quote_asset(
            market.amm, 
            quote_amount, 
            swap_direction, 
            now,
            market.amm.base_spread > 0
        )
        
        base_amount_change = abs(base_amount_acquired)            
        initial_quote_asset_amount_closed = (
            market_position.quote_asset_amount * base_amount_change / abs(prev_base_amount)
        )
        market_position.quote_asset_amount -= initial_quote_asset_amount_closed
        market_position.base_asset_amount += base_amount_acquired

        if market_position.base_asset_amount > 0:
            assert(base_amount_acquired<=0)
            market.base_asset_amount_long += base_amount_acquired
        else:
            assert(base_amount_acquired>=0)
            market.base_asset_amount_short += base_amount_acquired 
        
        market.base_asset_amount += base_amount_acquired
        market.amm.net_base_asset_amount += base_amount_acquired
        
        # compute pnl 
        if market_position.base_asset_amount > 0:
            pnl = quote_amount - initial_quote_asset_amount_closed
        else:
            pnl = initial_quote_asset_amount_closed - quote_amount
                    
        # add to collateral 
        user.collateral = calculate_updated_collateral(
            user.collateral, pnl 
        )

        return base_amount_acquired, quote_asset_amount_surplus
        
    def update_position_with_quote_asset_amount(
        self, 
        quote_amount, 
        direction, 
        user, 
        market_position,
        market
    ):
        increase_position = (
            market_position.base_asset_amount == 0 or 
            market_position.base_asset_amount > 0 and direction == PositionDirection.LONG or 
            market_position.base_asset_amount < 0 and direction == PositionDirection.SHORT 
        )
        
        if increase_position:
            _, quote_asset_amount_surplus = self.increase(
                quote_amount, 
                direction, 
                market_position, 
                market 
            )
        else: 
            base_value_in_quote = driftpy.math.positions.calculate_base_asset_value(
                market, 
                market_position
            )
            
            if base_value_in_quote > quote_amount:
                _, quote_asset_amount_surplus = self.reduce(
                    direction, 
                    quote_amount, 
                    user, 
                    market_position, 
                    market                     
                )
                potentially_risk_increasing = False
                reduce_only = True
            else: 
                # print('CLOSING THEN INCREASING', self.time)
                quote_after_close = quote_amount - base_value_in_quote
                # close current position 
                _, quote_asset_amount_surplus = self.close(market, user, market_position)
                # increase in new direction 
                _, quote_asset_amount_surplus2 = self.increase(quote_after_close, direction, market_position, market)

                quote_asset_amount_surplus += quote_asset_amount_surplus2

        return quote_asset_amount_surplus 

    def close(
        self, 
        market, 
        user, 
        market_position
    ):
        direction_to_close = {
            True: PositionDirection.SHORT,
            False: PositionDirection.LONG,
        }[market_position.base_asset_amount > 0]
        
        swap_direction = {
            PositionDirection.SHORT: SwapDirection.ADD,
            PositionDirection.LONG: SwapDirection.REMOVE
        }[direction_to_close]
        
        quote_amount_acquired, quote_asset_amount_surplus = swap_base_asset(
            market.amm, 
            market_position.base_asset_amount, 
            swap_direction,
            self.time,
            market.amm.base_spread > 0            
        )

        # compute pnl 
        pnl = calculate_pnl(
            quote_amount_acquired,
            market_position.quote_asset_amount, 
            swap_direction
        )

        # update collateral 
        user.collateral = calculate_updated_collateral(
            user.collateral, 
            pnl,
        )
        
        # update market 
        market.open_interest -= 1        
        market_position.quote_asset_amount = 0

        if market_position.base_asset_amount > 0:
            market.base_asset_amount_long -= market_position.base_asset_amount
        else:
            market.base_asset_amount_short -= market_position.base_asset_amount 

        market.base_asset_amount -= market_position.base_asset_amount
        market.amm.net_base_asset_amount -= market_position.base_asset_amount
        
        # update market position 
        market_position.last_cumulative_funding_rate = 0
        market_position.base_asset_amount = 0

        return quote_amount_acquired, quote_asset_amount_surplus
    
    def check_fails_margin_requirements(
        self, 
        user
    ):
        margin_requirement = 0 
        unrealized_pnl = 0 
        
        for i in range(len(self.markets)): 
            market: Market = self.markets[i]
            position: MarketPosition = user.positions[i]
            
            unrealized_pnl = driftpy.math.positions.calculate_position_pnl(
                market, position
            )
            base_asset_value = driftpy.math.positions.calculate_base_asset_value(
                market, 
                position
            )
            
            margin_requirement += base_asset_value * market.margin_ratio_initial
            unrealized_pnl += unrealized_pnl
        
        total_collateral = calculate_updated_collateral(
            user.collateral, 
            unrealized_pnl
        )
        margin_requirement = margin_requirement / MARGIN_PRECISION
        fails_margin_requirement = total_collateral < margin_requirement
        
        return fails_margin_requirement
    
    def close_position(
        self, 
        user_index, 
        market_index, 
    ):
        market = self.markets[market_index]
        user: User = self.users[user_index]
        market_position: MarketPosition = user.positions[market_index]
        
        assert user.lp_positions[market_index].lp_tokens == 0, 'Cannot lp and close position'
        
        # do nothing 
        if market_position.base_asset_amount == 0:
            return self 
        
        quote_amount, quote_asset_amount_surplus = self.close(
            market, 
            user, 
            market_position,
        )
        
        # apply user fee
        exchange_fee = abs(quote_amount * float(self.fee_structure.numerator) / float(self.fee_structure.denominator))
        user.collateral = max(0, user.collateral - exchange_fee)
        market.total_exchange_fees += exchange_fee 
        market.total_mm_fees += quote_asset_amount_surplus

        #todo: match rust impl
        total_fee = exchange_fee + quote_asset_amount_surplus        
        market.amm.total_fee += total_fee
        market.amm.total_fee_minus_distributions += total_fee

        return self 
        
    def open_position(
        self, 
        direction, 
        user_index, 
        quote_amount, 
        market_index, 
    ):
        if (quote_amount == 0):
            return self 
        self_copy = copy.deepcopy(self) # incase of reverts 
        now = self.time
        
        user: User = self.users[user_index]
        market_position: MarketPosition = user.positions[market_index]
        market = self.markets[market_index]
        oracle_price = market.amm.oracle.get_price(now)
                
        assert user.lp_positions[market_index].lp_tokens == 0, 'Cannot lp and open position'
                
        budget_cost = max(0, (market.amm.total_fee_minus_distributions/1e6)/2)
        # print('BUDGET_COST', budget_cost)

        if 'PreFreePeg' in market.amm.strategies:
            freepeg_cost, base_scale, quote_scale, new_peg = calculate_freepeg_cost(market, oracle_price, budget_cost)
            # if abs(freepeg_cost) > 1e-4:
                # print('NOW:', now)
                # print(freepeg_cost)
                # print('freepegging:', 'scales:', base_scale, quote_scale,  'peg:', market.amm.peg_multiplier, '->', new_peg)

            # print('NOW:', now)
            market.amm.base_asset_reserve *= base_scale
            market.amm.quote_asset_reserve *= quote_scale
            market.amm.peg_multiplier = new_peg  
            market.amm.sqrt_k = np.sqrt(market.amm.base_asset_reserve * market.amm.quote_asset_reserve)
            market.amm.total_fee_minus_distributions -= int(freepeg_cost*1e6)
            # print('new price:', calculate_mark_price(market))
            # print('post fpeg:', market.amm.base_asset_reserve, market.amm.quote_asset_reserve)
        elif 'PrePeg' in market.amm.strategies:
            new_peg = calculate_peg_multiplier(market.amm, oracle_price, now, budget_cost=budget_cost)
            if new_peg != market.amm.peg_multiplier:
                print('repegging', market.amm.peg_multiplier, '->', new_peg)
                self.repeg(market, new_peg)        
        
        mark_price_before = calculate_mark_price(market)
        
        # settle funding rates
        self.settle_funding_rates(user_index)

        # update oracle twaps 
        oracle_is_valid = True # TODO 
        if oracle_is_valid: 
            update_oracle_twap(market.amm, now)
        
        # print(market.amm.last_oracle_price)
        # update position 
        quote_asset_amount_surplus = self.update_position_with_quote_asset_amount(
            quote_amount, direction, user, market_position, market
        )
            
        # TODO: 
        # risk increasing ? ... 
        # trail fails if: oracle divergence, ... 
        # limit order?         
        mark_price_after = calculate_mark_price(market)

        # check if meets margin requirements -- if not revert 
        fails_margin_requirement = self.check_fails_margin_requirements(user)
        if fails_margin_requirement: 
            return self_copy
            
        # apply user fee
        # print(quote_amount, float(self.fee_structure.numerator) / float(self.fee_structure.denominator))
        exchange_fee = abs(quote_amount * float(self.fee_structure.numerator) / float(self.fee_structure.denominator))
        assert(exchange_fee > 0)
        user.collateral = max(0, user.collateral - exchange_fee)
        user.total_fee_paid += exchange_fee
        user.total_fee_rebate += quote_asset_amount_surplus
        
        market.total_exchange_fees += exchange_fee 
        market.total_mm_fees += quote_asset_amount_surplus

        #todo: match rust impl
        total_fee = exchange_fee + quote_asset_amount_surplus
        market.amm.total_fee += total_fee
        market.amm.total_fee_minus_distributions += total_fee
        
        ## try to update funding rate 
        self.update_funding_rate(market_index)

        price_change = mark_price_before - mark_price_after
        update_mark_price_std(market.amm, self.time, price_change)
        
        return self 
    
    def to_df(self):
        json = self.to_json()
        timestamp = json.pop("timestamp")
        df = pd.DataFrame(json, index=[timestamp])
        return df 
    
    def to_json(self):
        data = {}
        
        # serialize markets
        now = self.time
        for market_index in range(len(self.markets)):
            prefix = f"m{market_index}" # m0 = 0th market
            market_data = self.markets[market_index].to_json(now)
            add_prefix(market_data, prefix)
            
            data = data | market_data # combine dicts
            
        # serialize users 
        for user_index in self.users.keys():
            prefix = f"u{user_index}" # u0 = 0th user
            user = self.users[user_index]
            user_data = user.to_json(self)
            add_prefix(user_data, prefix)
            
            data = data | user_data
            
        # log timestamp 
        data["timestamp"] = self.time
            
        return data 
     
def add_prefix(data: dict, prefix: str):
    for key in list(data.keys()): 
        data[f"{prefix}_{key}"] = data.pop(key)
