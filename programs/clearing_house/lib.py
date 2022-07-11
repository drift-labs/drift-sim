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
from programs.clearing_house.state.user import User, MarketPosition, LPMetrics

MARGIN_PRECISION = 10_000 # expo = -4

def max_collateral_change(user, delta):
    if user.collateral + delta < 0: 
        print("warning neg collateral...")
        delta = -user.collateral
    return delta

@dataclass
class ClearingHouse: 
    total_usdc = 0 
    markets: list[Market]
    fee_structure: FeeStructure
    users: dict = field(default_factory=dict)
    usernames: dict = field(default_factory=dict)
    time: int = 0 
    name: str = ''
    
    def __post_init__(self):
        for index, market in enumerate(self.markets):
            market.market_index = index
            
    def deposit_user_collateral(
        self,
        user_index, 
        collateral_amount, 
        name='u'
    ):
        # initialize user if not already 
        if user_index not in self.users: 
            market_positions = [MarketPosition() for _ in range(len(self.markets))]
            self.users[user_index] = User(
                user_index=user_index,
                collateral=0, 
                positions=market_positions, 
            )
            self.usernames[user_index] = f"{name}{user_index}"

        user = self.users[user_index]
        user.collateral += collateral_amount
        user.cumulative_deposits += collateral_amount
        self.total_usdc += collateral_amount
        
        return self 
    
    
    ## adds quote amount to take on the AMM's position (virtually) and have 
    ## a proportion of the future fees earned -- tracked by a lp_token
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
        user_lp_token_amount = int(
            quote_amount * AMM_TO_QUOTE_PRECISION_RATIO 
            / 2 
            / (market.amm.peg_multiplier / PEG_PRECISION)
        )
        
        reserve_scale =  (market.amm.total_lp_tokens + user_lp_token_amount) \
            / market.amm.total_lp_tokens
       
        # update k 
        market.amm.base_asset_reserve *= reserve_scale
        market.amm.quote_asset_reserve *= reserve_scale
        market.amm.sqrt_k += user_lp_token_amount

        market.amm.total_lp_tokens = market.amm.sqrt_k
        
        # record other metrics
        user_position = user.positions[market_index]
        user_position.lp_tokens = user_lp_token_amount
        user_position.last_cumulative_lp_funding = market.amm.cumulative_lp_funding
        user_position.last_net_base_asset_amount = market.amm.net_base_asset_amount
        user_position.last_total_fee_minus_distributions = market.amm.total_fee_minus_distributions
        
        return self 
    
    def settle_lp(
        self, 
        market_index: int, 
        user_index: int, 
    ):
        user: User = self.users[user_index]
        market: Market = self.markets[market_index]
        lp_position: MarketPosition = user.positions[market_index]
        if lp_position.lp_tokens < 0:
            print("warning: trying to settle user who is not an lp")
            return self 
        
        self.settle_lp_tokens(
            user, 
            market, 
            lp_position.lp_tokens # settle the full amount 
        )

        return self

    def get_lp_metrics(
        self, 
        lp_position: MarketPosition, 
        lp_tokens_to_settle: int, 
        market: Market
    ) -> LPMetrics: 
        total_lp_tokens = market.amm.sqrt_k;
        lp_token_amount = lp_tokens_to_settle

        # give them portion of fees since deposit 
        change_in_fees = market.amm.total_fee_minus_distributions - lp_position.last_total_fee_minus_distributions
        assert change_in_fees >= 0, "lp loses money"

        fee_payment = change_in_fees * lp_token_amount / total_lp_tokens  

        # give them portion of funding since deposit
        change_in_funding = (
            market.amm.cumulative_lp_funding 
            - lp_position.last_cumulative_lp_funding  
        ) / AMM_TO_QUOTE_PRECISION_RATIO # in quote 
        funding_payment = change_in_funding * lp_token_amount / total_lp_tokens  

        # give them the amm position  
        amm_net_position_change = (
            lp_position.last_net_base_asset_amount -
            market.amm.net_base_asset_amount 
        )

        market_baa = 0 
        market_qaa = 0 
        unsettled_pnl = 0 

        if amm_net_position_change != 0: 
            direction_to_close = {
                True: SwapDirection.REMOVE,
                False: SwapDirection.ADD,
            }[amm_net_position_change > 0]
            
            new_quote_asset_reserve, _ = calculate_swap_output(
                abs(amm_net_position_change), 
                market.amm.base_asset_reserve,
                direction_to_close,
                market.amm.sqrt_k
            )

            base_asset_amount = (
                amm_net_position_change
                * lp_token_amount 
                / total_lp_tokens
            )

            # someone goes long => amm_quote_position_change > 0
            amm_quote_position_change = (
                new_quote_asset_reserve -
                market.amm.quote_asset_reserve
            ) 

            # amm_quote_position_change > 0 then we need to increase cost basis 
            # market_position.quote_asset_amount is used for PnL 
            quote_asset_amount = int(
                amm_quote_position_change
                * (lp_token_amount / total_lp_tokens)
            ) * market.amm.peg_multiplier / AMM_TIMES_PEG_TO_QUOTE_PRECISION_RATIO
            quote_asset_amount = abs(quote_asset_amount)
           
            min_baa = market.amm.minimum_base_asset_trade_size
            min_qaa = market.amm.minimum_quote_asset_trade_size

            if abs(base_asset_amount) > min_baa and quote_asset_amount > min_qaa: 
                market_baa = base_asset_amount
                market_qaa = quote_asset_amount
            else:
                print('warning market position to small')
                print(f"{base_asset_amount} {min_baa} : {quote_asset_amount} {min_qaa}")
                unsettled_pnl = -market.amm.minimum_quote_asset_trade_size
            
        lp_metrics = LPMetrics(
            base_asset_amount=market_baa, 
            quote_asset_amount=market_qaa, 
            fee_payment=fee_payment, 
            funding_payment=funding_payment, 
            unsettled_pnl=unsettled_pnl
        )

        return lp_metrics
        
    ## converts the current virtual lp position into a real position 
    ## without burning lp tokens 
    def settle_lp_tokens(
        self, 
        user: User, 
        market: Market, 
        lp_token_amount: int, 
    ):
        lp_position = user.positions[market.market_index]
        lp_metrics = self.get_lp_metrics(lp_position, lp_token_amount, market)

        lp_position.base_asset_amount += lp_metrics.base_asset_amount
        lp_position.quote_asset_amount += lp_metrics.quote_asset_amount

        lp_pnl = lp_metrics.fee_payment + lp_metrics.funding_payment
        user.collateral += lp_pnl
        market.amm.total_fee_minus_distributions -= lp_metrics.fee_payment
    
        lp_position.last_net_base_asset_amount = market.amm.net_base_asset_amount
        lp_position.last_total_fee_minus_distributions = market.amm.total_fee_minus_distributions
        lp_position.last_cumulative_funding_rate = market.amm.cumulative_lp_funding

    ## burns the lp tokens, earns fees+funding, 
    ## and takes on the AMM's position (for realz)
    def remove_liquidity(
        self, 
        market_index: int, 
        user_index: int, 
        lp_token_amount: int, 
    ):
        user: User = self.users[user_index]
        market: Market = self.markets[market_index]
        lp_position: MarketPosition = user.positions[market_index]
        
        assert lp_position.lp_tokens >= 0, "need lp tokens to remove"
        assert lp_token_amount <= lp_position.lp_tokens, "trying to remove too much liquidity"
     
        # tmp
        assert lp_token_amount == lp_position.lp_tokens, "can only burn full lp tokens"

        # settle them 
        self.settle_lp_tokens(
            user, 
            market, 
            lp_token_amount
        )

        market_position: MarketPosition = user.positions[market_index]
        market_position.lp_tokens -= lp_token_amount

        if market_position.base_asset_amount > 0:
            market_position.last_cumulative_funding_rate = market.amm.cumulative_funding_rate_long
        else: 
            market_position.last_cumulative_funding_rate = market.amm.cumulative_funding_rate_short
        
        # update market shit
        market.amm.net_base_asset_amount += market_position.base_asset_amount
        market.open_interest += 1 

        total_lp_tokens = market.amm.sqrt_k
        reserve_scale = (total_lp_tokens - lp_token_amount) / total_lp_tokens 
        
        market.amm.base_asset_reserve *= reserve_scale
        market.amm.quote_asset_reserve *= reserve_scale
        market.amm.sqrt_k -= lp_token_amount

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
            mark_twap = update_mark_twap(market.amm, now) # not MARK_PRICE
            oracle_twap = update_oracle_twap(market.amm, now) # not MARK_PRICE
            
            price_spread = mark_twap - oracle_twap
                        
            max_price_spread = oracle_twap / 33 # 3% of oracle price
            clamped_price_spread = np.clip(price_spread, -max_price_spread, max_price_spread)
                    
            adjustment = 24 ## 24 slots of funding period time till full payback -- hardcode for now
            funding_rate = int(clamped_price_spread * FUNDING_PRECISION / adjustment)
            
            market.amm.cumulative_funding_rate_long += funding_rate
            market.amm.cumulative_funding_rate_short += funding_rate
                        
            market.amm.last_funding_rate = funding_rate
            market.amm.last_funding_rate_ts = now     
            
            # track lp funding 
            # TODO: double check compute lp funding 
            market_net_position = -market.amm.net_base_asset_amount # AMM_RSERVE_PRE
            market_funding_rate = funding_rate # FUNDING_PRECISION 
        
            market_funding_payment = (
                market_funding_rate 
                * market_net_position 
                / FUNDING_PRECISION
            )
            market.amm.cumulative_lp_funding += market_funding_payment
            
        return self
        
    def settle_funding_rates(
        self, 
        user_index
    ):
        now = self.time 
        user: User = self.users[user_index]
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
                
                total_funding_payment += funding_payment / AMM_TO_QUOTE_PRECISION_RATIO
                
                position.last_cumulative_funding_rate = amm_cumulative_funding_rate
                position.last_funding_rate_ts = now 
                
        # dont pay more than the total number of fees 
        total_funding_payment = min(total_funding_payment, market.amm.total_fee_minus_distributions)
        total_funding_payment = max_collateral_change(user, total_funding_payment)
        
        market.amm.total_fee_minus_distributions -= total_funding_payment # market pays funding
        user.collateral += total_funding_payment

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
        # print('increase:', base_amount_acquired/1e13, quote_amount/1e6)
        
        market_position.base_asset_amount += base_amount_acquired
        
        if base_amount_acquired > 0:
            market.base_asset_amount_long += base_amount_acquired
            market.amm.quote_asset_amount_long += quote_amount
        else:
            market.base_asset_amount_short += base_amount_acquired 
            market.amm.quote_asset_amount_short += quote_amount

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
            market.amm.quote_asset_amount_long -= quote_amount
        else:
            assert(base_amount_acquired>=0)
            market.base_asset_amount_short += base_amount_acquired 
            market.amm.quote_asset_amount_short -= quote_amount

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
        swap_direction = {
            True: SwapDirection.ADD,
            False: SwapDirection.REMOVE,
        }[market_position.base_asset_amount > 0]
        
        quote_amount_acquired, quote_asset_amount_surplus = swap_base_asset(
            market.amm, 
            market_position.base_asset_amount, 
            swap_direction,
            self.time,
            market.amm.base_spread > 0            
        )
        
        # print('close:', quote_amount_acquired/1e6)

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
       
        # # TODO: tmp
        # user.collateral += pnl 
        # market.amm.total_fee_minus_distributions -= pnl
    
        # update market 
        market.open_interest -= 1        
        market_position.quote_asset_amount = 0

        if market_position.base_asset_amount > 0:
            market.base_asset_amount_long -= market_position.base_asset_amount
            market.amm.quote_asset_amount_long -= quote_amount_acquired
        else:
            market.base_asset_amount_short -= market_position.base_asset_amount 
            market.amm.quote_asset_amount_short -= quote_amount_acquired

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
        
        assert user.positions[market_index].lp_tokens == 0, 'Cannot lp and close position'
        
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
        exchange_fee = max_collateral_change(user, -exchange_fee)
        user.collateral += exchange_fee
        
        positive_exchange_fee = -exchange_fee
        market.amm.total_fee_minus_distributions += positive_exchange_fee
        
        user.total_fee_paid += positive_exchange_fee
        
        market.total_exchange_fees += positive_exchange_fee
        market.total_mm_fees += quote_asset_amount_surplus

        #todo: match rust impl
        total_fee = exchange_fee + quote_asset_amount_surplus
        market.amm.total_fee += total_fee

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
        assert user.positions[market_index].lp_tokens == 0, 'Cannot lp and open position'

        mark_price_before = calculate_mark_price(market)

        fee_pool = (market.amm.total_fee_minus_distributions/1e6) - (market.amm.total_fee/1e6)/2
        budget_cost = max(0, fee_pool)
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
            market.amm.terminal_quote_asset_reserve = market.amm.sqrt_k**2 / (market.amm.base_asset_reserve+market.amm.net_base_asset_amount)
            market.amm.total_fee_minus_distributions -= int(freepeg_cost*1e6)
            # print('new price:', calculate_mark_price(market))
            # print('post fpeg:', market.amm.base_asset_reserve, market.amm.quote_asset_reserve)
        elif 'PrePeg' in market.amm.strategies:
            new_peg = calculate_peg_multiplier(market.amm, oracle_price, now, budget_cost=budget_cost)
            if new_peg != market.amm.peg_multiplier:
                print('repegging', market.amm.peg_multiplier, '->', new_peg)
                self.repeg(market, new_peg)        
        
        mark_price_before_2 = calculate_mark_price(market)
        update_mark_price_std(market.amm, self.time, abs(mark_price_before-mark_price_before_2))

        user: User = self.users[user_index]
        market_position: MarketPosition = user.positions[market_index]
                        
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
            print(f'WARNING: u{user_index} margin requirement not met, reverting...')
            return self_copy
            
        # apply user fee
        # print(quote_amount, float(self.fee_structure.numerator) / float(self.fee_structure.denominator))
        exchange_fee = -abs(quote_amount * float(self.fee_structure.numerator) / float(self.fee_structure.denominator))
        exchange_fee = max_collateral_change(user, exchange_fee)
        assert(exchange_fee < 0)

        total_fee = exchange_fee + quote_asset_amount_surplus
        user.collateral += total_fee
        user.total_fee_paid += -exchange_fee
        user.total_fee_rebate += quote_asset_amount_surplus
        
        #TODO: match rust impl
        market.amm.total_fee_minus_distributions -= total_fee
        market.amm.total_fee -= total_fee

        ## try to update funding rate 
        self.update_funding_rate(market_index)

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
            prefix = self.usernames[user_index]
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
