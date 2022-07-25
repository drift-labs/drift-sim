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
from sim.helpers import compute_total_collateral, close_all_users

import numpy as np 
import pandas as pd

import unittest

#%%
def default_set_up(self, n_users=1, default_collateral=1000, bq_ar=1e6):
    length = 10 
    self.default_collateral = default_collateral * QUOTE_PRECISION    
    self.funding_period = 60 # every 60 ts 
    
    self.prices = [.5] * length # .5$ oracle 
    self.timestamps = np.arange(length)
    self.oracle = Oracle(prices=self.prices, timestamps=self.timestamps)

    # mark price = 1$ 
    self.amm = AMM(
        oracle=self.oracle, 
        base_asset_reserve=int(bq_ar) * AMM_RESERVE_PRECISION, 
        quote_asset_reserve=int(bq_ar) * AMM_RESERVE_PRECISION,
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
        default_set_up(self, n_users=2, default_collateral=10_000_000, bq_ar=100) 

    def test_funding(self): 
        ch: ClearingHouse = self.clearing_house
        market = ch.markets[0]

        full_amm_position_quote = market.amm.amm_lp_shares
        ch = ch.deposit_user_collateral(1, full_amm_position_quote)
        init_collateral = compute_total_collateral(ch)

        ch.add_liquidity(
            0, 1, full_amm_position_quote
        )

        # user goes long (should get paid)
        ch.open_position(
           PositionDirection.LONG, 
           0, 
           100 * QUOTE_PRECISION, 
           0 
        )
        ch.change_time(5)

        # update funding rates 
        ch.update_funding_rate(0)
        ch.settle_funding_rates(0)

        # check to make sure they got the correct shares 
        lp_share = ch.users[1].positions[0].lp_shares / ch.markets[0].amm.total_lp_shares
        assert lp_share == 0.5

        ch.remove_liquidity(
            0, 1
        )

        ch.change_time(5)

        ch = close_all_users(ch)[0]
        end_collateral = compute_total_collateral(ch)
        assert math.isclose(init_collateral, end_collateral, abs_tol=1e7) 

    def test_deposit_remove_liquidity(self):
        ch = self.clearing_house 
        user: User = ch.users[0]

        _user = copy.deepcopy(user)
        _userj = user.to_json(ch)

        deposit_amount = 10_000_000 * QUOTE_PRECISION
        ch = ch.add_liquidity(0, 0, deposit_amount)
        self.assertGreater(user.positions[0].lp_shares, _user.positions[0].lp_shares)
        
        ch = ch.remove_liquidity(
            0, 0, user.positions[0].lp_shares
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

        deposit_amount = 1e6 * QUOTE_PRECISION
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
            quote_amount=1e6 * QUOTE_PRECISION,
            market_index=0,
            timestamp=ch.time,
        ).run(ch)
        ch.change_time(1)
        
        prev_collateral = user.collateral    
        
        # remove_liquidity lp position         
        ch = ch.remove_liquidity(
            0, 0, user.positions[0].lp_shares
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
        self.assertEqual(user.positions[0].lp_shares, 0)
  
    def test_lp(self):
        # make bar larger for larger trades
        
        for user_close_first in [True, False]:
            for trade_direction in [PositionDirection.LONG, PositionDirection.SHORT]:
                for trade_size in [1e4, 1e6, 1e7]:
                    for p in [1., .75, .5, .25, .01]:
                        default_set_up(self, n_users=2, default_collateral=0, bq_ar=1e8) 
                        self._test_lp(p, trade_size, trade_direction, user_close_first)
    
    def _test_lp(self, lp_percent, trade_size, trade_direction, user_close_first):

        print('---')
        print(lp_percent, trade_size, trade_direction, user_close_first)
        print('---')

        ch: ClearingHouse = self.clearing_house
        market: Market = ch.markets[0]
        
        lp_index = 0
        user_index = 1 
        
        lp: User = ch.users[lp_index]
        user: User = ch.users[user_index]
        
        full_amm_position_quote = market.amm.amm_lp_shares 
        percent_amm_position_quote = int(full_amm_position_quote * lp_percent)

        # setup users        
        ch = ch.deposit_user_collateral(
            lp_index, 
            percent_amm_position_quote
        ).deposit_user_collateral(
            1, 
            trade_size * QUOTE_PRECISION
        )
        
        # record total collateral pre trades     
        init_collateral = compute_total_collateral(ch)

        ch = ch.add_liquidity(
            0, lp_index, percent_amm_position_quote
        )
        ch = ch.open_position(
            trade_direction, user_index, trade_size * QUOTE_PRECISION, 0
        )

        lp_ratio = lp.positions[0].lp_shares / market.amm.total_lp_shares
        print('lp ratio', lp_ratio)

        ch = ch.remove_liquidity(
            0, lp_index, lp.positions[0].lp_shares
        )
        print("baa diff", lp.positions[0].base_asset_amount + user.positions[0].base_asset_amount * lp_ratio)
        print("qaa diff", lp.positions[0].quote_asset_amount - user.positions[0].quote_asset_amount * lp_ratio)
        
        if user_close_first:
            ch = ch.close_position(
                user_index, 0    
            ).close_position(
                lp_index, 0    
            )
        else: 
            ch = ch.close_position(
                lp_index, 0    
            ).close_position(
                user_index, 0    
            )

        close_all_users(ch)

        ch = self.clearing_house
        lp_fee_payments = 0 
        market_fees = 0 
        market: Market = ch.markets[0]
        for (_, user) in ch.users.items(): 
            position: MarketPosition = user.positions[0]
            lp_fee_payments += position.lp_fee_payments
            market_fees += position.market_fee_payments
        total_payments = lp_fee_payments + market.amm.total_fee_minus_distributions
        print("fee diff", abs(total_payments) - abs(market_fees))

        # %%
        lp_funding_payments = 0 
        market_funding = 0 
        market: Market = ch.markets[0]
        for (_, user) in ch.users.items(): 
            position: MarketPosition = user.positions[0]
            lp_funding_payments += position.lp_funding_payments
            market_funding += position.market_funding_payments
        total_payments = market.amm.lp_funding_payment + lp_funding_payments
        print("funding diff:", market_funding + total_payments)

        final_collateral = compute_total_collateral(ch)
        abs_difference = abs(init_collateral - final_collateral)
        print('abs diff:', abs_difference)
        self.assertLessEqual(abs_difference, 1)
        

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
        self.assertGreater(market.amm.net_base_asset_amount, 0)        
        
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
        self.assertGreater(market.amm.net_base_asset_amount, 0)        
        
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
        
    def test_reserves(self):
        ch = self.clearing_house
        market = ch.markets[0]
        trade_size = 100 * QUOTE_PRECISION
        
        init_bar, init_qar = market.amm.base_asset_reserve, market.amm.quote_asset_reserve
        ch = ch.deposit_user_collateral(
            user_index=0, 
            collateral_amount=trade_size
        ).open_position(
            PositionDirection.LONG, 
            0, trade_size, 0
        )
        
        assert market.amm.base_asset_reserve < init_bar
        assert market.amm.quote_asset_reserve > init_qar
        
        ch = ch.close_position(0, 0)
        new_bar, new_qar = market.amm.base_asset_reserve, market.amm.quote_asset_reserve
        
        # print(init_bar, init_qar)
        # print(new_bar, new_qar)
        
        self.assertEqual(init_bar, new_bar)
        self.assertEqual(init_qar, new_qar)
        
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
        self.assertAlmostEqual(market_position.quote_asset_amount, current_base_quote_value, delta=2)
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
        self.assertAlmostEqual(market_position.quote_asset_amount, current_base_quote_value, delta=1)
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
        self.assertGreater(market.amm.total_fee_minus_distributions, prev_fees)

import math 
class TestCollateral(unittest.TestCase):
        
    def setUp(self):
        default_set_up(self, n_users=2)

    def test_long_short(self):
        """
        user goes long 
        user goes closes long 
        user pnl = market fees 
        """
        ch = self.clearing_house
        user0: User = ch.users[0]
        market: Market = ch.markets[0]

        init_collateral = user0.collateral
        ch = ch.open_position(
            PositionDirection.LONG, 0, 100 * QUOTE_PRECISION, 0
        ).close_position(0, 0)

        math.isclose(
            (user0.collateral + market.amm.total_fee_minus_distributions) / 1e6, 
            init_collateral / 1e6, 
        )

    def test_two_upnl(self):
        """
        u0 longs 
        u1 shorts 
        u0 closes (pays pnl to u0) 
        u1 closes (pnl from u1) 
        """

        ch = self.clearing_house
        user0: User = ch.users[0]
        user1: User = ch.users[1]
        market: Market = ch.markets[0]

        total_collateral = user0.collateral + user1.collateral

        total_collateral = user0.collateral + user1.collateral

        ch.open_position(
            PositionDirection.LONG, 0, 100 * QUOTE_PRECISION, 0
        ).open_position(
            PositionDirection.SHORT, 1, 100 * QUOTE_PRECISION, 0
        ).close_position(
            0, 0
        ).close_position(
            1, 0
        )

        expected_total_collateral = user0.collateral + user1.collateral + market.amm.total_fee_minus_distributions
        math.isclose(total_collateral/1e6, expected_total_collateral/1e6, abs_tol=1e-3)

    def test_two_upnl_smaller(self):
        """
        u0 longs 
        u1 shorts smaller amount [price moves down]
        u0 closes (pays pnl to u0) [negative pnl is smaller]
        u1 closes (pnl from u1) [positive pnl is smaller]
        """
        ch = self.clearing_house 

        user0: User = ch.users[0]
        user1: User = ch.users[1]
        market: Market = ch.markets[0]
        total_collateral = user0.collateral + user1.collateral

        ch.open_position(
            PositionDirection.LONG, 0, 100 * QUOTE_PRECISION, 0
        ).open_position(
            PositionDirection.SHORT, 1, 50 * QUOTE_PRECISION, 0
        )

        ch = ch.close_position(
            0, 0
        ).close_position(
            1, 0
        )

        expected_total_collateral = user0.collateral + user1.collateral + market.amm.total_fee_minus_distributions
        math.isclose(total_collateral/1e6, expected_total_collateral/1e6, abs_tol=1e-3)

if __name__ == '__main__':
    unittest.main()

# %%
