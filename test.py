import sys
sys.path.insert(0, 'driftpy/src/')

import driftpy

from driftpy.math.trade import *
from driftpy.math.positions import *
from driftpy.math.amm import *
from driftpy.math.market import *

from driftpy.types import *
from driftpy.constants.numeric_constants import *

from programs.clearing_house.math.pnl import *
from programs.clearing_house.math.amm import *
from programs.clearing_house.state import *
from programs.clearing_house.lib import * 
from programs.clearing_house.state import * 
from sim.events import * 

import numpy as np 
import pandas as pd

import unittest

#%%
def default_set_up(self, n_users=1, default_collateral=1000):
    length = 10 
    self.default_collateral = default_collateral * QUOTE_PRECISION    
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

    for index in range(n_users):
        self.clearing_house = (
            self.clearing_house
            .deposit_user_collateral(
                user_index=index, 
                collateral_amount=self.default_collateral
            )        
        )

#%%
class TestLP(unittest.TestCase):
    
    def setUp(self):
        default_set_up(self, n_users=2, default_collateral=10_000_000) 
        
    def test_deposit_remove_liquidity(self):
        ch = self.clearing_house 
        user: User = ch.users[0]

        _user = copy.deepcopy(user)
        _userj = user.to_json(ch)

        deposit_amount = 100 * QUOTE_PRECISION
        ch = ch.add_liquidity(0, 0, deposit_amount)
        
        self.assertEqual(user.locked_collateral, deposit_amount)
        self.assertGreater(user.lp_positions[0].lp_tokens, _user.lp_positions[0].lp_tokens)
        
        ch = ch.remove_liquidity(
            0, 0, user.lp_positions[0].lp_tokens
        )
        _userj2 = user.to_json(ch)
        
        # nothing should change
        for k in _userj: 
            if np.isnan(_userj[k]) and np.isnan(_userj2[k]):
                continue
            self.assertEqual(_userj[k], _userj2[k])
            
    def test_fee_profit_lp(self):
        ch = self.clearing_house 
        user: User = ch.users[0]
        market: Market = ch.markets[0]

        deposit_amount = 100 * QUOTE_PRECISION
        ch = ch.add_liquidity(0, 0, deposit_amount)
        
        # do some trades
        for _ in range(100):
            ch = OpenPositionEvent(
                user_index=1, 
                direction='long',
                quote_amount=100 * QUOTE_PRECISION,
                market_index=0,
                timestamp=ch.time,
            ).run(ch)
            ch.change_time(1)
            
            ch = OpenPositionEvent(
                user_index=1, 
                direction='short',
                quote_amount=100 * QUOTE_PRECISION,
                market_index=0,
                timestamp=ch.time,
            ).run(ch)
            ch.change_time(1)
        
        ch = OpenPositionEvent(
            user_index=1, 
            direction='long',
            quote_amount=100 * QUOTE_PRECISION,
            market_index=0,
            timestamp=ch.time,
        ).run(ch)
        ch.change_time(1)
        
        prev_collateral = user.collateral    
        
        # remove_liquidity lp position         
        ch = ch.remove_liquidity(
            0, 0, user.lp_positions[0].lp_tokens
        )
        ch.change_time(1)
        
        # user is now short -- took it from the amm 
        market_position: MarketPosition = user.positions[0]
        self.assertLess(market_position.base_asset_amount, 0)
        self.assertEqual(
            market_position.last_cumulative_funding_rate, 
            market.amm.cumulative_funding_rate_short
        )
        
        # should have made money from fees 
        self.assertGreater(user.collateral, prev_collateral)
        self.assertEqual(user.lp_positions[0].lp_tokens, 0)
        
    def test_full_lp(self):
        ch = self.clearing_house 
        market: Market = self.clearing_house.markets[0]
        self._test_n_percent_lp(1.0)
        
        # close LP
        ch = ch.close_position(0, 0)
        # close user
        ch = ch.close_position(1, 0)
                
        # market is now balanced
        self.assertEqual(
            market.amm.net_base_asset_amount,
            0
        )
        self.assertEqual(
            market.amm.base_asset_reserve,
            market.amm.quote_asset_reserve,
        )
    
    def test_half_lp(self):
        self._test_n_percent_lp(0.5)
    
    def test_twenty_lp(self):
        self._test_n_percent_lp(0.2)
    
    def test_twenty_five_lp(self):
        self._test_n_percent_lp(0.25)
        
    def test_twenty_five_lp(self):
        self._test_n_percent_lp(0.19)
        
    def test_a_lot_lp(self):
        for p in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
            self._test_n_percent_lp(p)
            self.setUp()
    
    def _test_n_percent_lp(self, percent):
        ch = self.clearing_house
        market: Market = ch.markets[0]
        lp: LPPosition = ch.users[0]
        user: User = ch.users[1]

        peg = market.amm.peg_multiplier / PEG_PRECISION
        sqrt_k = market.amm.sqrt_k / 1e13
        full_amm_position_quote = sqrt_k * peg * 2 * 1e6
        percent_amm_position_quote = full_amm_position_quote * percent
        
        ch = ch.add_liquidity(
            0, 0, percent_amm_position_quote
        )
        
        # user has percent of amm's tokens
        self.assertAlmostEqual(
            ch.markets[0].amm.lp_tokens / 1e6, 
            ch.markets[0].amm.total_lp_tokens * (1 - percent) / 1e6, 
            places=2
        )
        self.assertAlmostEqual(
            lp.lp_positions[0].lp_tokens,
            ch.markets[0].amm.total_lp_tokens * percent
        )
        self.assertAlmostEqual(
            lp.lp_positions[0].lp_tokens + ch.markets[0].amm.lp_tokens,
            ch.markets[0].amm.total_lp_tokens
        )
        
        # new user goes long 
        ch = ch.open_position(
            PositionDirection.LONG, 
            1, 
            10_000 * QUOTE_PRECISION, 
            0
        )
        
        # removes lp 
        prev_market_baa = ch.markets[0].amm.net_base_asset_amount
        amount_should_take = prev_market_baa * percent
        ch = ch.remove_liquidity(
            0, 0, lp.lp_positions[0].lp_tokens
        )
        
        user_position = user.positions[0]
        lp_position = lp.positions[0]
        
        self.assertEqual(
            lp_position.quote_asset_amount / percent,
            user_position.quote_asset_amount
        )
        self.assertAlmostEqual(
            -lp_position.base_asset_amount / percent / 1e13,
            user_position.base_asset_amount / 1e13
        )
        self.assertAlmostEqual(
            lp_position.base_asset_amount / 1e13,
            -amount_should_take / 1e13,
        )
        self.assertAlmostEqual(
            (prev_market_baa - amount_should_take) / 1e13, 
            ch.markets[0].amm.net_base_asset_amount / 1e13
        )
        

class TestTWAPs(unittest.TestCase):
    
    def setUp(self):
        default_set_up(self)
        
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
        default_set_up(self)

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
        default_set_up(self)

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
        quote_amount = 100
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

        # oracle > mark 
        # funding = mark_twap - oracle_twap < 0
        # assert that the funding rate is correct        
        self.assertEqual(market.amm.last_funding_rate_ts, 1 * self.funding_period)
        # shorts pay long = negative funding rate
        self.assertLess(market.amm.cumulative_funding_rate_long, 0)
        self.assertLess(market.amm.cumulative_funding_rate_short, 0)
        
        # assert user gets paid by long funding rate 
        prev_collateral = user.collateral 
        ch = ch.settle_funding_rates(user_index)
        self.assertGreater(user.collateral, prev_collateral)
        
class TestOracle(unittest.TestCase):
    def setUp(self):
        self.prices = np.arange(5)
        self.timestamps = np.arange(5)
        self.oracle = Oracle(prices=self.prices, timestamps=self.timestamps)

    def test_oracle(self):
        for i in range(len(self.prices)):
            self.assertEqual(self.oracle.get_price(i), self.prices[i])

        for i in range(len(self.prices)):
            self.assertEqual(self.oracle.get_price(i+0.5), self.prices[i])
            
        for i in range(len(self.prices)):
            self.assertEqual(self.oracle.get_price(i+0.99), self.prices[i])


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
