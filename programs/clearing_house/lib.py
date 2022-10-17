#%%
import copy 
import numpy as np 
import pandas as pd
from dataclasses import dataclass, field

import driftpy
from driftpy.math.market import calculate_mark_price, calculate_freepeg_cost
from driftpy.math.amm import calculate_peg_multiplier
from driftpy.types import PositionDirection, PerpPosition, SwapDirection
from driftpy.constants.numeric_constants import * 

from programs.clearing_house.math.amm import *
from programs.clearing_house.math.lp import *
from programs.clearing_house.math.pnl import *
from programs.clearing_house.controller.funding import *
from programs.clearing_house.controller.position import *
from programs.clearing_house.controller.amm import *
from programs.clearing_house.controller.lp import *

from programs.clearing_house.state import *
from programs.clearing_house.helpers import add_prefix


@dataclass
class ClearingHouse: 
    total_usdc = 0 
    markets: list[SimulationMarket]
    fee_structure: FeeStructure
    users: dict = field(default_factory=dict)
    usernames: dict = field(default_factory=dict)
    time: int = 0 
    name: str = ''
            
    def change_time(self, time_delta):
        self.time = self.time + time_delta
        return self 

    def deposit_user_collateral(
        self,
        user_index, 
        collateral_amount, 
        name='u'
    ):
        # initialize user if not already 
        if user_index not in self.users: 
            positions = [MarketPosition(user_index) for _ in range(len(self.markets))]
            self.users[user_index] = User(
                user_index=user_index,
                collateral=0, 
                positions=positions, 
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
        token_amount: int, 
    ):
        
        user: User = self.users[user_index]
        market: SimulationMarket = self.markets[market_index]
        user_position = user.positions[market_index]

        # TODO: margin requirements ... 
        
        if user_position.lp_shares > 0:
            settle_lp_shares(user, market, user_position.lp_shares)
        else: 
            user_position.last_cumulative_base_asset_amount_with_amm_per_lp = market.amm.cumulative_base_asset_amount_with_amm_per_lp
            user_position.last_cumulative_funding_rate_lp = market.amm.cumulative_funding_payment_per_lp
            user_position.last_cumulative_fee_per_lp = market.amm.cumulative_fee_per_lp

        # increment token amount
        user_position.lp_shares += token_amount

        # update k
        new_sqrt_k = market.amm.sqrt_k + token_amount
        bar, qar, sqrt_k = get_updated_k_result(market, new_sqrt_k)
        market.amm.base_asset_reserve = bar 
        market.amm.quote_asset_reserve = qar 
        market.amm.sqrt_k = sqrt_k

        # track new lp 
        market.amm.total_lp_shares += token_amount
        
        return self 
    
    def settle_lp(
        self, 
        market_index: int, 
        user_index: int, 
    ):
        user: User = self.users[user_index]
        market: SimulationMarket = self.markets[market_index]
        position: PerpPosition = user.positions[market_index]

        if position.lp_shares <= 0:
            print("warning: trying to settle user who is not an lp")
            return self
        
        settle_lp_shares(
            user, 
            market, 
            position.lp_shares # settle the full amount 
        )

        return self

    ## burns the lp tokens, earns fees+funding, 
    ## and takes on the AMM's position (for realz)
    def remove_liquidity(
        self, 
        market_index: int, 
        user_index: int, 
        lp_token_amount: int = -1, 
    ):
        user: User = self.users[user_index]
        market: SimulationMarket = self.markets[market_index]
        position: PerpPosition = user.positions[market_index]

        if lp_token_amount == -1:
            lp_token_amount = position.lp_shares

        if position.lp_shares == 0: 
            return self
        
        assert position.lp_shares >= 0, "need lp tokens to remove"
        assert lp_token_amount <= position.lp_shares, f"trying to remove too much liquidity: {lp_token_amount} > {position.lp_shares}"

        # settle them 
        settle_lp_shares(
            user,
            market,
            position.lp_shares # settle the full amount 
        )

        # settle funding on any existing market positions
        settle_funding_rates(user, self.markets, self.time)

        # give them the market position of the portion 
        position: PerpPosition = user.positions[market_index]
        base_amount_acquired = position.lp_base_asset_amount * lp_token_amount / position.lp_shares
        quote_amount = position.lp_quote_asset_amount * lp_token_amount / position.lp_shares

        # lp position => market position
        position.lp_base_asset_amount -= base_amount_acquired 
        position.lp_quote_asset_amount -= quote_amount

        # need to be careful when the position flips
        is_long_reduce = position.base_asset_amount > 0 and base_amount_acquired < 0
        is_short_reduce = position.base_asset_amount < 0 and base_amount_acquired > 0
        abs_acquired = abs(base_amount_acquired) 
        abs_current_baa = abs(position.base_asset_amount)

        is_increase = (position.base_asset_amount > 0 and base_amount_acquired > 0) or (position.base_asset_amount < 0 and base_amount_acquired < 0)
        is_reduce = (is_long_reduce and abs_acquired < abs_current_baa) or (is_short_reduce and abs_acquired < abs_current_baa) 
        is_flip = (is_long_reduce and abs_acquired > abs_current_baa) or (is_short_reduce and abs_acquired > abs_current_baa) 
        is_new_position = position.base_asset_amount == 0 and base_amount_acquired != 0
        is_close = position.base_asset_amount + base_amount_acquired == 0 and position.base_asset_amount != 0

        if is_new_position or is_increase:  
            # print("new position/increase")
            track_new_base_assset(
                position,
                market,
                base_amount_acquired,
                quote_amount, 
                is_lp_update=True,
            )
        elif is_reduce: 
            # print("reduce")
            # compute pnl 
            baa_change = abs(abs_acquired - abs_current_baa)
            quote_closed = (
                position.quote_asset_amount * baa_change / abs_current_baa
            )
            if position.base_asset_amount > 0: 
                pnl = quote_amount - quote_closed 
            else: 
                pnl = quote_closed - quote_amount
            pnl = max_collateral_change(user, pnl)
            user.collateral += pnl 

            track_new_base_assset(
                position,
                market,
                base_amount_acquired,
                -quote_closed, 
                is_lp_update=True,
            )
        elif is_close:
            # print("close")
            # compute pnl 
            if position.base_asset_amount > 0: 
                pnl = quote_amount - position.quote_asset_amount
            else: 
                pnl = position.quote_asset_amount - quote_amount
            pnl = max_collateral_change(user, pnl)
            user.collateral += pnl 

            # close position 
            track_new_base_assset(
                position,
                market,
                base_amount_acquired,
                -position.quote_asset_amount, 
                is_lp_update=True,
            )
        elif is_flip: 
            # close 
            quote_closed = quote_amount * abs_current_baa / abs_acquired
            if position.base_asset_amount > 0:
                pnl = quote_closed - position.quote_asset_amount
            else:
                pnl = position.quote_asset_amount - quote_closed
            pnl = max_collateral_change(user, pnl)
            user.collateral += pnl

            track_new_base_assset(
                position,
                market,
                -position.base_asset_amount,
                -position.quote_asset_amount, 
                is_lp_update=True,
            )
            
            # increase 
            new_baa_sign = 1 if base_amount_acquired > 0 else -1 
            new_baa = new_baa_sign * abs(abs_acquired - abs_current_baa)
            new_qaa = quote_amount - quote_closed
            track_new_base_assset(
                position,
                market,
                new_baa, 
                new_qaa, 
                is_lp_update=True,
            )
        elif base_amount_acquired == 0: 
            # assert quote_amount == 0, (base_amount_acquired, quote_amount)
            # do nothing
            # somtimes theres dust positions from rounding errors
            user.collateral += quote_amount
            pass 
        else: 
            print("baa (acquir, curr):", base_amount_acquired, position.base_asset_amount)
            print("qaa (acquir, curr):", quote_amount, position.quote_asset_amount)
            assert False, "shouldnt be called"
       
        position.lp_shares -= lp_token_amount
        market.amm.total_lp_shares -= lp_token_amount

        # update k
        new_sqrt_k = market.amm.sqrt_k - lp_token_amount
        bar, qar, sqrt_k = get_updated_k_result(market, new_sqrt_k)
        market.amm.base_asset_reserve = bar 
        market.amm.quote_asset_reserve = qar 
        market.amm.sqrt_k = sqrt_k

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
            # print('updating funding ...')
            mark_twap = update_mark_twap(market.amm, now) # not MARK_PRICE
            oracle_twap = update_oracle_twap(market.amm, now) # not MARK_PRICE
            
            # print(mark_twap, oracle_twap)
            price_spread = mark_twap - oracle_twap 
                        
            max_price_spread = oracle_twap / 33 # 3% of oracle price
            clamped_price_spread = np.clip(price_spread, -max_price_spread, max_price_spread)
                    
            adjustment = 1 ## 24 slots of funding period time till full payback -- hardcode for now
            funding_rate = int(clamped_price_spread * FUNDING_RATE_BUFFER / adjustment)
            
            market.amm.cumulative_funding_rate_long += funding_rate
            market.amm.cumulative_funding_rate_short += funding_rate
                        
            market.amm.last_funding_rate = funding_rate
            market.amm.last_funding_rate_ts = now
            
            market_net_position = -market.amm.base_asset_amount_with_amm # AMM_RSERVE_PRE
            market_funding_rate = funding_rate # FUNDING_RATE_BUFFER 
            market_funding_payment = (
                market_funding_rate 
                * market_net_position 
                / FUNDING_RATE_BUFFER
                / AMM_TO_QUOTE_PRECISION_RATIO
            )
            
            funding_slice = market_funding_payment * AMM_RESERVE_PRECISION / market.amm.total_lp_shares
            # market.amm.lp_funding_payment += -1 * funding_slice * market.amm.amm_lp_shares / 1e13 
            market.amm.cumulative_funding_payment_per_lp += funding_slice

        return self
        

    def increase(
        self, 
        quote_amount: float, 
        direction: PositionDirection, 
        position: PerpPosition, 
        market: SimulationMarket
    ):         
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
        
        # market.base_asset_amount += base_amount_acquired
        track_new_base_assset(position, market, base_amount_acquired, quote_amount)
                
        return base_amount_acquired, quote_asset_amount_surplus
    

    def repeg(self, amm: SimulationAMM, new_peg: int):
        # print(amm, new_peg)
        cost = calculate_repeg_cost(amm, new_peg)
        amm.peg_multiplier = new_peg
        amm.total_fee_minus_distributions -= cost*QUOTE_PRECISION

        # market.total_fees -= cost*1e6
        # market.total_mm_fees -= cost*1e6
        # market.amm.total_fee -= cost*1e6
    
    def reduce(
        self, 
        direction: PositionDirection, 
        quote_amount: float, 
        user: User, 
        position: PerpPosition, 
        market: SimulationMarket
    ):         
        swap_direction = {
            PositionDirection.LONG: SwapDirection.ADD,
            PositionDirection.SHORT: SwapDirection.REMOVE
        }[direction]
        
        prev_base_amount = position.base_asset_amount
        
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
            position.quote_asset_amount * base_amount_change / abs(prev_base_amount)
        )

        track_new_base_assset(
            position, 
            market, 
            base_amount_acquired, 
            -initial_quote_asset_amount_closed
        )

        # compute pnl 
        if position.base_asset_amount > 0:
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
        position,
        market
    ):
        increase_position = (
            position.base_asset_amount == 0 or 
            position.base_asset_amount > 0 and direction == PositionDirection.LONG or 
            position.base_asset_amount < 0 and direction == PositionDirection.SHORT 
        )
        
        if increase_position:
            _, quote_asset_amount_surplus = self.increase(
                quote_amount, 
                direction, 
                position, 
                market 
            )
        else: 
            base_value_in_quote = driftpy.math.positions.calculate_base_asset_value(
                market, 
                position
            )
            
            if base_value_in_quote > quote_amount:
                _, quote_asset_amount_surplus = self.reduce(
                    direction, 
                    quote_amount, 
                    user, 
                    position, 
                    market                     
                )
                potentially_risk_increasing = False
                reduce_only = True
            else: 
                # print('CLOSING THEN INCREASING', self.time)
                quote_after_close = quote_amount - base_value_in_quote
                # close current position 
                _, quote_asset_amount_surplus = self.close(market, user, position)
                # increase in new direction 
                _, quote_asset_amount_surplus2 = self.increase(quote_after_close, direction, position, market)

                quote_asset_amount_surplus += quote_asset_amount_surplus2

        return quote_asset_amount_surplus 

    def close(
        self, 
        market, 
        user, 
        position
    ):
        swap_direction = {
            True: SwapDirection.ADD,
            False: SwapDirection.REMOVE,
        }[position.base_asset_amount > 0]
        
        quote_amount_acquired, quote_asset_amount_surplus = swap_base_asset(
            market.amm, 
            position.base_asset_amount, 
            swap_direction,
            self.time,
            market.amm.base_spread > 0            
        )
        # print('close:', quote_amount_acquired/1e6)

        # compute pnl
        pnl = calculate_pnl(
            quote_amount_acquired,
            position.quote_asset_amount,
            swap_direction
        )

        # update collateral
        user.collateral = calculate_updated_collateral(
            user.collateral,
            pnl,
        )

        # update market 
        track_new_base_assset(
           position, 
           market, 
           -position.base_asset_amount, 
           -position.quote_asset_amount
        )

        return quote_amount_acquired, quote_asset_amount_surplus
    
    def check_fails_margin_requirements(
        self, 
        user
    ):
        margin_requirement = 0 
        unrealized_pnl = 0 
        
        for i in range(len(self.markets)): 
            market: SimulationMarket = self.markets[i]
            position: PerpPosition = user.positions[i]
            
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
        position: PerpPosition = user.positions[market_index]
        
        settle_funding_rates(user, self.markets, self.time)

        if position.lp_shares > 0:
            lp_shares = position.lp_shares
            self.remove_liquidity(market_index, user_index)
            self.add_liquidity(market_index, user_index, lp_shares)

        # do nothing 
        if position.base_asset_amount == 0:
            return self 
        
        quote_amount, quote_asset_amount_surplus = self.close(
            market, 
            user, 
            position,
        )
        market.amm.total_fee_minus_distributions += quote_asset_amount_surplus

        # apply user fee
        exchange_fee = -abs(quote_amount * float(self.fee_structure.numerator) / float(self.fee_structure.denominator))        
        self.apply_fee(exchange_fee, user, market) # TODO: incorp surplus 

        ## try to update funding rate 
        self.update_funding_rate(market_index)

        # exchange_fee = max_collateral_change(user, -exchange_fee)
        # user.collateral += exchange_fee
        # positive_exchange_fee = -exchange_fee
        # market.amm.total_fee_minus_distributions += positive_exchange_fee
        # user.total_fee_paid += positive_exchange_fee
        # market.total_exchange_fees += positive_exchange_fee
        # market.total_mm_fees += quote_asset_amount_surplus
        # #todo: match rust impl
        # total_fee = exchange_fee + quote_asset_amount_surplus
        # market.amm.total_fee += total_fee
        # if market.amm.total_lp_shares > 0:
        #     market.amm.cumulative_fee_per_lp += total_fee / market.amm.total_lp_shares

        return self 

    def settle_funding_rates(
        self,
        user_index: int
    ):
        settle_funding_rates(self.users[user_index], self.markets, self.time)
        return self
        
    def open_position(
        self, 
        direction, 
        user_index, 
        quote_amount, 
        market_index, 
        ioc: bool = False
    ):
        if (quote_amount == 0):
            return self 

        self_copy = copy.deepcopy(self) # incase of reverts 
        now = self.time
        
        user: User = self.users[user_index]
        position: PerpPosition = user.positions[market_index]
        market = self.markets[market_index]
        oracle_price = market.amm.oracle.get_price(now)
        # assert user.positions[market_index].lp_shares == 0, 'Cannot lp and open position'

        mark_price_before = calculate_mark_price(market)

        fee_pool = (market.amm.total_fee_minus_distributions/QUOTE_PRECISION) - (market.amm.total_fee/QUOTE_PRECISION)/2
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
            market.amm.terminal_quote_asset_reserve = market.amm.sqrt_k**2 / (market.amm.base_asset_reserve+market.amm.base_asset_amount_with_amm)
            market.amm.total_fee_minus_distributions -= int(freepeg_cost*QUOTE_PRECISION)
            # print('new price:', calculate_mark_price(market))
            # print('post fpeg:', market.amm.base_asset_reserve, market.amm.quote_asset_reserve)
        elif 'PrePeg' in market.amm.strategies:
            new_peg = calculate_peg_multiplier(market.amm, oracle_price, now, budget_cost=budget_cost)
            if new_peg != market.amm.peg_multiplier:
                print('repegging', market.amm.peg_multiplier, '->', new_peg)
                self.repeg(market.amm, new_peg)        
        
        mark_price_before_2 = calculate_mark_price(market)
        update_mark_price_std(market.amm, self.time, abs(mark_price_before-mark_price_before_2))

        user: User = self.users[user_index]
        position: PerpPosition = user.positions[market_index]
                        
        # settle funding rates
        settle_funding_rates(user, self.markets, self.time)

        # update oracle twaps 
        oracle_is_valid = True # TODO 
        if oracle_is_valid: 
            update_oracle_twap(market.amm, now)
        
        # print(market.amm.last_oracle_price)
        # update position 
        quote_asset_amount_surplus = self.update_position_with_quote_asset_amount(
            quote_amount, direction, user, position, market
        )
        # print("quote surplus:", quote_asset_amount_surplus)
        market.amm.total_fee_minus_distributions += quote_asset_amount_surplus
            
        # TODO: 
        # risk increasing ? ... 
        # trail fails if: oracle divergence, ... 
        # limit order?         

        # check if meets margin requirements -- if not revert 
        fails_margin_requirement = self.check_fails_margin_requirements(user)
        if fails_margin_requirement: 
            print(f'WARNING: u{user_index} margin requirement not met, reverting...')
            return self_copy
            
        # apply user fee
        # print(quote_amount, float(self.fee_structure.numerator) / float(self.fee_structure.denominator))
        exchange_fee = -abs(quote_amount * float(self.fee_structure.numerator) / float(self.fee_structure.denominator))
        exchange_fee = max_collateral_change(user, exchange_fee)
        self.apply_fee(exchange_fee, user, market)

        # total_fee = exchange_fee + quote_asset_amount_surplus
        # user.collateral += total_fee
        # user.total_fee_paid += -exchange_fee
        # user.total_fee_rebate += quote_asset_amount_surplus
        
        # #TODO: match rust impl
        # market.amm.total_fee_minus_distributions -= total_fee
        # market.amm.total_fee -= total_fee

        ## try to update funding rate 
        self.update_funding_rate(market_index)

        return self 

    def apply_fee(self, fee, user, market):
        fee = max_collateral_change(user, fee)
        assert fee < 0, f"fee: {fee}"
        user.collateral += fee 
        user.positions[market.market_index].market_fee_payments += fee 

        fee_slice = fee * AMM_RESERVE_PRECISION / market.amm.total_lp_shares
        
        # print('-- new fee payment --')
        # print('total fee:', fee)
        # print('market fee:', fee_slice / 1e13 * market.amm.amm_lp_shares)
        # print('other lp fee:', fee_slice / 1e13 * (market.amm.total_lp_shares - market.amm.amm_lp_shares))

        market.amm.total_fee_minus_distributions -= fee_slice / AMM_RESERVE_PRECISION * market.amm.amm_lp_shares
        market.amm.cumulative_fee_per_lp -= fee_slice

        market.amm.total_fee -= fee 
    
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
     

# %%