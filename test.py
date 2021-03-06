#%%
import sys
sys.path.insert(0, 'driftpy/src/')

import driftpy

from driftpy.math.amm import (
    calculate_swap_output, 
    calculate_amm_reserves_after_swap, 
    get_swap_direction
)
from driftpy.math.trade import calculate_trade_slippage, calculate_target_price_trade, calculate_trade_acquired_amounts
from driftpy.math.positions import calculate_base_asset_value, calculate_position_pnl
from driftpy.types import PositionDirection, AssetType, MarketPosition, SwapDirection
from driftpy.math.market import calculate_mark_price
from driftpy.constants.numeric_constants import AMM_TIMES_PEG_TO_QUOTE_PRECISION_RATIO, PEG_PRECISION
from driftpy.math.amm import calculate_price
from driftpy.constants.numeric_constants import *

from programs.clearing_house.math.pnl import *
from programs.clearing_house.math.amm import *
from programs.clearing_house.state import *

import json 
import numpy as np 
import pandas as pd
import matplotlib.pyplot as plt 

from dataclasses import dataclass, field
from solana.publickey import PublicKey

#%%
from programs.clearing_house.lib import * 
from programs.clearing_house.state import * 

import unittest

#%%
class TestTWAPs(unittest.TestCase):
    
    def setUp(self):
        self.default_collateral = 1_000 * QUOTE_PRECISION
        self.funding_period = 1 
        
        length = 10 
        self.prices = [.5] * length # .5$ oracle 
        self.timestamps = np.arange(length)
        self.oracle = Oracle(prices=self.prices, timestamps=self.timestamps)

        # mark price = 1$ 
        self.amm = AMM(
            oracle=self.oracle, 
            # low liquidity 
            base_asset_reserve=1_000 * AMM_RESERVE_PRECISION, 
            quote_asset_reserve=1_000 * AMM_RESERVE_PRECISION,
            peg_multiplier=1 * PEG_PRECISION, 
            funding_period=self.funding_period
        )
        self.market = Market(self.amm)
        self.fee_structure = FeeStructure(numerator=1, denominator=100)
        self.clearing_house = ClearingHouse([self.market], self.fee_structure)     
        
        self.clearing_house = (
            self.clearing_house
            .deposit_user_collateral(
                user_index=0, 
                collateral_amount=self.default_collateral
            )        
        )
        
    def mark(self):
        user_index = 0
        market_index = 0 
    
        ch = self.clearing_house
        
        user = ch.users[user_index]
        market = ch.markets[market_index]
                
        prev_twap = market.amm.last_mark_price_twap
        prev_twap_ts = market.amm.last_mark_price_twap_ts
        prev_mark_price = calculate_mark_price(market)

        # increment time
        ch = ch.change_time(market.amm.funding_period + 1)
                            
        # large price movement 
        quote_amount = 10_000
        ch = ch.open_position(
            PositionDirection.LONG, 
            user_index, 
            quote_amount * QUOTE_PRECISION, 
            market_index
        )
        
        user = ch.users[user_index]
        market = ch.markets[market_index]
        
        twap = market.amm.last_mark_price_twap
        twap_ts = market.amm.last_mark_price_twap_ts
        mark_price = calculate_mark_price(market)
         
        # twap increases
        self.assertGreater(twap, prev_twap)
        self.assertGreater(mark_price, prev_mark_price)
        # timstamp is correct 
        self.assertGreater(twap_ts, prev_twap_ts)
        # twap is smaller than mark price (bc of weighted average) 
        self.assertLess(twap, mark_price)
    
class TestClearingHouseFundingTimestamp(unittest.TestCase):
        
    def setUp(self):
        self.default_collateral = 1_000 * QUOTE_PRECISION
        
        length = 10 
        self.funding_period = 60 # every 60 ts 
        
        self.prices = [.5] * length # .5$ oracle 
        self.timestamps = np.arange(length)
        self.oracle = Oracle(prices=self.prices, timestamps=self.timestamps)

        # mark price = 1$ 
        self.amm = AMM(
            oracle=self.oracle, 
            base_asset_reserve=1_000_000 * AMM_RESERVE_PRECISION, 
            quote_asset_reserve=1_000_000 * AMM_RESERVE_PRECISION,
            peg_multiplier=1 * PEG_PRECISION, 
            funding_period=self.funding_period
        )
        self.market = Market(self.amm)
        self.fee_structure = FeeStructure(numerator=1, denominator=100)
        self.clearing_house = ClearingHouse([self.market], self.fee_structure)        

        self.clearing_house = (
            self.clearing_house
            .deposit_user_collateral(
                user_index=0, 
                collateral_amount=self.default_collateral
            )        
        )

    def test_funding_ts(self):
        ch = self.clearing_house
        
        user = ch.users[0]
        market: Market = ch.markets[0]
        
        prev_funding_ts = market.amm.last_funding_rate_ts
        
        delta = 5 
        ch = ch.change_time(delta)
        ch = ch.update_funding_rate(market_index=0)
        
        # funding ts shouldnt change 
        market = ch.markets[0]
        self.assertEqual(prev_funding_ts, market.amm.last_funding_rate_ts)
        
        # increment time by period 
        ch = ch.change_time(self.funding_period - delta + 1)
        ch = ch.update_funding_rate(market_index=0)
        market = ch.markets[0]
        
        # funding ts should update now 
        self.assertEqual(market.amm.last_funding_rate_ts, ch.time)

class TestClearingHousePositiveFunding(unittest.TestCase):
        
    def setUp(self):
        self.default_collateral = 1_000 * QUOTE_PRECISION
        
        length = 10 
        self.funding_period = 1 
        
        self.prices = [.5] * length # .5$ oracle 
        self.timestamps = np.arange(length)
        self.oracle = Oracle(prices=self.prices, timestamps=self.timestamps)

        # mark price = 1$ 
        self.amm = AMM(
            oracle=self.oracle, 
            base_asset_reserve=1_000_000 * AMM_RESERVE_PRECISION, 
            quote_asset_reserve=1_000_000 * AMM_RESERVE_PRECISION,
            peg_multiplier=1 * PEG_PRECISION, 
            funding_period=self.funding_period
        )
        self.market = Market(self.amm)
        self.fee_structure = FeeStructure(numerator=1, denominator=100)
        self.clearing_house = ClearingHouse([self.market], self.fee_structure)        
        self.clearing_house = (
            self.clearing_house
            .deposit_user_collateral(
                user_index=0, 
                collateral_amount=self.default_collateral
            )        
        )


    def test_positive_funding_short(self):
        # open new short position
        user_index = 0
        market_index = 0 
    
        ch = self.clearing_house
        user = ch.users[user_index]
        market = ch.markets[market_index]
        
        # go short 
        quote_amount = 1
        ch = ch.open_position(
            PositionDirection.SHORT, 
            user_index, 
            quote_amount * QUOTE_PRECISION, 
            market_index
        )

        prev_collateral = user.collateral
                
        # fast forward time 
        ch = ch.change_time(1 * self.funding_period)
        ch = ch.update_funding_rate(market_index)
        ch = ch.settle_funding_rates(user_index)
        
        user = ch.users[user_index]
        market = ch.markets[market_index]

        self.assertGreater(user.collateral, prev_collateral)
        
        # assert that the funding rate is correct        
        self.assertEqual(market.amm.last_funding_rate_ts, 1 * self.funding_period)
        # shorts pay long = negative funding rate
        self.assertGreater(market.amm.cumulative_funding_rate_long, 0)
        self.assertGreater(market.amm.cumulative_funding_rate_short, 0)
        
    def test_positive_funding_long(self):
        # open new long position
        user_index = 0
        market_index = 0 
        
        ch = self.clearing_house
        user = ch.users[user_index]
        market = ch.markets[market_index]
        
        quote_amount = 1
        ch = ch.open_position(
            PositionDirection.LONG, 
            user_index, 
            quote_amount * QUOTE_PRECISION, 
            market_index
        )
                
        self.assertGreater(market.base_asset_amount_long, 0)
        self.assertGreater(market.base_asset_amount, 0)        
        
        # fast forward time 
        ch = ch.change_time(1 * self.funding_period)
        ch = ch.update_funding_rate(market_index)
        
        user = ch.users[user_index]
        market = ch.markets[market_index]

        # assert that the funding rate is correct        
        self.assertEqual(market.amm.last_funding_rate_ts, 1 * self.funding_period)
        
        # shorts pay long = negative funding rate
        self.assertGreater(market.amm.cumulative_funding_rate_long, 0)
        self.assertGreater(market.amm.cumulative_funding_rate_short, 0)
        
        # assert user gets paid by long funding rate 
        prev_collateral = user.collateral 
        ch = ch.settle_funding_rates(user_index)
        self.assertLess(user.collateral, prev_collateral)

class TestClearingHouseNegativeFunding(unittest.TestCase):
    
    def setUp(self):
        self.default_collateral = 1_000 * QUOTE_PRECISION
        
        length = 10 
        self.funding_period = 1 
        
        self.prices = [2] * length # 2$ oracle 
        self.timestamps = np.arange(length)
        self.oracle = Oracle(prices=self.prices, timestamps=self.timestamps)

        # mark price = 1$ 
        self.amm = AMM(
            oracle=self.oracle, 
            base_asset_reserve=1_000_000 * AMM_RESERVE_PRECISION, 
            quote_asset_reserve=1_000_000 * AMM_RESERVE_PRECISION,
            peg_multiplier=1 * PEG_PRECISION, 
            funding_period=self.funding_period
        )
        self.market = Market(self.amm)
        self.fee_structure = FeeStructure(numerator=1, denominator=100)
        self.clearing_house = ClearingHouse([self.market], self.fee_structure)

        self.clearing_house = (
            self.clearing_house
            .deposit_user_collateral(
                user_index=0, 
                collateral_amount=self.default_collateral
            )        
        )

    def test_negative_funding_short(self):
        # open new short position
        user_index = 0
        market_index = 0 
    
        ch = self.clearing_house
        user = ch.users[user_index]
        market = ch.markets[market_index]
        
        # go short 
        quote_amount = 1
        ch = ch.open_position(
            PositionDirection.SHORT, 
            user_index, 
            quote_amount * QUOTE_PRECISION, 
            market_index
        )

        prev_collateral = user.collateral
                
        # fast forward time + do funding things 
        ch = (ch
            .change_time(1 * self.funding_period)
            .update_funding_rate(market_index)
            .settle_funding_rates(user_index)
        )

        # funding should decrease collateral 
        self.assertLess(user.collateral, prev_collateral)
        
        # assert that the funding rate is correct        
        self.assertEqual(market.amm.last_funding_rate_ts, 1 * self.funding_period)
        # shorts pay long = negative funding rate
        self.assertLess(market.amm.cumulative_funding_rate_long, 0)
        self.assertLess(market.amm.cumulative_funding_rate_short, 0)
        
    def test_negative_funding_long(self):
        # open new long position
        user_index = 0
        market_index = 0 
    
        ch = self.clearing_house      
        user = ch.users[user_index]
        market = ch.markets[market_index]
        
        quote_amount = 1
        ch = ch.open_position(
            PositionDirection.LONG, 
            user_index, 
            quote_amount * QUOTE_PRECISION, 
            market_index
        )
        
        self.assertGreater(market.base_asset_amount_long, 0)
        self.assertGreater(market.base_asset_amount, 0)        
        
        # fast forward time 
        ch = ch.change_time(1 * self.funding_period)
        ch = ch.update_funding_rate(market_index)
        
        user = ch.users[user_index]
        market = ch.markets[market_index]

        # assert that the funding rate is correct        
        self.assertEqual(market.amm.last_funding_rate_ts, 1 * self.funding_period)
        # shorts pay long = negative funding rate
        self.assertLess(market.amm.cumulative_funding_rate_long, 0)
        self.assertLess(market.amm.cumulative_funding_rate_short, 0)
        
        # assert user gets paid by long funding rate 
        prev_collateral = user.collateral 
        ch = ch.settle_funding_rates(user_index)
        self.assertGreater(user.collateral, prev_collateral)
        

#%%
class TestClearingHousePositions(unittest.TestCase):
    
    def setUp(self):
        self.prices = np.arange(5)
        self.timestamps = np.arange(5)
        self.oracle = Oracle(prices=self.prices, timestamps=self.timestamps)

        self.default_collateral = 100 * QUOTE_PRECISION

        # initial price = 1$ 
        self.amm = AMM(
            oracle=self.oracle, 
            base_asset_reserve=1_000_000 * AMM_RESERVE_PRECISION, 
            quote_asset_reserve=1_000_000 * AMM_RESERVE_PRECISION,
            peg_multiplier=1 * PEG_PRECISION, 
            funding_period=60
        )
        self.market = Market(self.amm)
        self.fee_structure = FeeStructure(numerator=1, denominator=100)
        self.clearing_house = ClearingHouse([self.market], self.fee_structure)
        
        self.clearing_house = (
            self.clearing_house
            .deposit_user_collateral(
                user_index=0, 
                collateral_amount=self.default_collateral
            )        
        )


    def test_oracle(self):
        for i in range(len(self.prices)):
            self.assertEqual(self.oracle.get_price(i), self.prices[i])

        for i in range(len(self.prices)):
            self.assertEqual(self.oracle.get_price(i+0.5), self.prices[i])
            
        for i in range(len(self.prices)):
            self.assertEqual(self.oracle.get_price(i+0.99), self.prices[i])

    def test_short_pnl(self):
        user_index = 0
        market_index = 0 
        
        ch = self.clearing_house
        user = ch.users[user_index]
        market = ch.markets[market_index]
        
        prev_collateral = user.collateral

        # user goes 1x short
        ch = ch.open_position(
            PositionDirection.SHORT, 
            user_index, 
            self.default_collateral, 
            market_index
        )
        
        # modify xy curve to 0.5$ 
        market = ch.markets[market_index] # updated market 
        market.amm.base_asset_reserve=2_000_000 * AMM_RESERVE_PRECISION
        market.amm.quote_asset_reserve=1_000_000 * AMM_RESERVE_PRECISION
        market.amm.sqrt_k = int((
            market.amm.base_asset_reserve * market.amm.quote_asset_reserve
        ) ** .5)
                        
        ch = ch.close_position(user_index, market_index)
        
        user = ch.users[user_index]        
        # 50% drop while short 
        self.assertAlmostEqual(user.collateral / prev_collateral, 1.5, delta=0.1)
            
    def test_long_pnl(self):
        user_index = 0
        market_index = 0 
        
        ch = self.clearing_house        
        user = ch.users[user_index]
        market = ch.markets[market_index]
        
        prev_market_position = user.positions[market_index]
        prev_collateral = user.collateral

        # user goes 1x long 
        ch = ch.open_position(
            PositionDirection.LONG, 
            user_index, 
            self.default_collateral, 
            market_index
        )
        
        # modify xy curve to 2$ 
        market = ch.markets[market_index] # updated market 
        market.amm.base_asset_reserve=1_000_000 * AMM_RESERVE_PRECISION
        market.amm.quote_asset_reserve=2_000_000 * AMM_RESERVE_PRECISION
        market.amm.sqrt_k = int((
            market.amm.base_asset_reserve * market.amm.quote_asset_reserve
        ) ** .5)
                        
        ch = ch.close_position(user_index, market_index)
        
        user = ch.users[user_index]
        market_position = user.positions[market_index]
        collateral = user.collateral
        
        self.assertAlmostEqual((collateral / prev_collateral), 2, delta=0.1)
        
    def test_margin_fail(self):
        user_index = 0
        market_index = 0     
        ch = self.clearing_house
                
        ch = ch.open_position(
            PositionDirection.LONG, 
            user_index, 
            50 * self.default_collateral, # 50x long -- should fail  
            market_index
        )
        
        # need to get the up to date state 
        user = ch.users[user_index]
        market_position = user.positions[market_index]
        
        self.assertEqual(market_position.base_asset_amount, 0) # should fail 

    # user goes short 
    # reduces position 
    # reduces position to zero 
    def test_short_long_user(self):
        user_index = 0
        market_index = 0     
        ch = self.clearing_house
        user = ch.users[user_index]
        
        market = ch.markets[market_index]
        market_position = user.positions[market_index]
        
        self.assertEqual(user.collateral, self.default_collateral)
        self.assertEqual(len(ch.users), 1)
        
        ### NONE -> SHORT
        prev_collateral = user.collateral
        prev_fees = market.amm.total_fee
        
        short_amount = 1
        ch = ch.open_position(
            PositionDirection.SHORT, 
            user_index, 
            short_amount * QUOTE_PRECISION, 
            market_index
        )
        
        # should be ~1:1 
        self.assertAlmostEqual(
            user.positions[market_index].base_asset_amount / AMM_RESERVE_PRECISION, 
            -short_amount, 
            delta=1e-4
        )
        # collateral decreases to pay for fees
        self.assertLess(user.collateral, prev_collateral)
        # market get fees 
        self.assertGreater(market.amm.total_fee, prev_fees)
        # base/quote reserves change 
        self.assertGreater(market.amm.base_asset_reserve, market.amm.quote_asset_reserve)
        
        ### SHORT -> LESS SHORT 
        prev_collateral = user.collateral
        prev_fees = market.amm.total_fee
        # close half the position 
        base_value = driftpy.math.positions.calculate_base_asset_value(
            market, 
            market_position
        )
        close_amount = base_value / 1.5
        prev_base_amount = user.positions[market_index].base_asset_amount
        
        ch = ch.open_position(
            PositionDirection.LONG, 
            user_index, 
            close_amount, 
            market_index
        )
        # position is reduced 
        self.assertLess(prev_base_amount, user.positions[market_index].base_asset_amount)
        # still short 
        self.assertLess(user.positions[market_index].base_asset_amount, 0)
        # collateral decreases to pay for fees
        self.assertLess(user.collateral, prev_collateral)
        # market get fees 
        self.assertGreater(market.amm.total_fee, prev_fees)
        
        # reverse position: SHORT -> LONG 
        prev_collateral = user.collateral
        prev_fees = market.amm.total_fee
        prev_base_amount = market_position.base_asset_amount
        current_base_quote_value = driftpy.math.positions.calculate_base_asset_value(
            market, 
            market_position
        ) 
        
        ch = ch.open_position(
            PositionDirection.LONG, 
            user_index, 
            current_base_quote_value * 2, 
            market_index
        )
        
        # position is closed
        self.assertGreater(market_position.base_asset_amount, 0)        
        self.assertEqual(market_position.quote_asset_amount, current_base_quote_value)
        # collateral decreases to pay for fees
        self.assertLess(user.collateral, prev_collateral)
        # market get fees
        self.assertGreater(market.amm.total_fee, prev_fees)
        
        ### LONG -> NONE 
        ch = ch.close_position(
            user_index, 
            market_index
        )
        
        # position is closed
        self.assertEqual(market_position.base_asset_amount, 0)        
        self.assertEqual(market_position.last_cumulative_funding_rate, 0)
        self.assertEqual(market_position.quote_asset_amount, 0)
        # collateral decreases to pay for fees
        self.assertLess(user.collateral, prev_collateral)
        # market get fees
        self.assertGreater(market.amm.total_fee, prev_fees)
        
    # user goes long 
    # reduces position 
    # reduces position to zero 
    def test_long_short_user(self):
        user_index = 0
        market_index = 0 

        ch = self.clearing_house
        user = ch.users[user_index]
    
        market = ch.markets[market_index]
        market_position = user.positions[market_index]
        
        self.assertEqual(user.collateral, self.default_collateral)
        self.assertEqual(len(ch.users), 1)
        
        ### TEST LONG
        prev_collateral = user.collateral
        prev_fees = market.amm.total_fee
        prev_oi = market.open_interest
        
        long_amount = 1 
        ch = ch.open_position(
            PositionDirection.LONG, 
            user_index, 
            long_amount * QUOTE_PRECISION, 
            market_index
        )
        
        # should be ~1:1 
        self.assertAlmostEqual(market_position.base_asset_amount / AMM_RESERVE_PRECISION, long_amount, delta=1e-4)
        
        # collateral decreases to pay for fees
        self.assertLess(user.collateral, prev_collateral)
        # market get fees 
        self.assertGreater(market.amm.total_fee, prev_fees)
        # base/quote reserves change 
        self.assertGreater(market.amm.quote_asset_reserve, market.amm.base_asset_reserve)
        # increase in oi 
        self.assertGreater(market.open_interest, prev_oi)
        
        ### LONG -> LESS LONG
        prev_collateral = user.collateral
        prev_fees = market.amm.total_fee
        # close half the position 
        close_amount = market_position.quote_asset_amount / 1.5
        prev_base_amount = market_position.base_asset_amount
        
        ch = ch.open_position(
            PositionDirection.SHORT, 
            user_index, 
            close_amount, 
            market_index
        )
        
        # position is reduced 
        self.assertLess(market_position.base_asset_amount, prev_base_amount)
        # still long
        self.assertGreater(market_position.base_asset_amount, 0)
        # collateral decreases to pay for fees
        self.assertLess(user.collateral, prev_collateral)
        # market get fees 
        self.assertGreater(market.amm.total_fee, prev_fees)
        
        # reverse position: LONG -> SHORT 
        prev_collateral = user.collateral
        prev_fees = market.amm.total_fee
        prev_base_amount = market_position.base_asset_amount
        current_base_quote_value = driftpy.math.positions.calculate_base_asset_value(
            market, 
            market_position
        ) 
        
        ch = ch.open_position(
            PositionDirection.SHORT, 
            user_index, 
            current_base_quote_value * 2, 
            market_index
        )
        
        # position is closed
        self.assertLessEqual(market_position.base_asset_amount, 0)        
        self.assertEqual(market_position.quote_asset_amount, current_base_quote_value)
        # collateral decreases to pay for fees
        self.assertLess(user.collateral, prev_collateral)
        # market get fees
        self.assertGreater(market.amm.total_fee, prev_fees)

        ### SHORT -CLOSE-> NONE 
        prev_collateral = user.collateral
        prev_fees = market.amm.total_fee
        close_amount = market_position.base_asset_amount
        
        ch = ch.close_position(
            user_index, 
            market_index
        )
        
        # position is closed
        self.assertEqual(market_position.base_asset_amount, 0)        
        self.assertEqual(market_position.last_cumulative_funding_rate, 0)
        self.assertEqual(market_position.quote_asset_amount, 0)
        # collateral decreases to pay for fees
        self.assertLess(user.collateral, prev_collateral)
        # market get fees
        self.assertGreater(market.amm.total_fee, prev_fees)

        
if __name__ == '__main__':
    unittest.main()

#%%
#%%
#%%
#%%
#%%
#%%