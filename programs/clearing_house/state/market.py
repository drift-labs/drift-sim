from dataclasses import dataclass, field
from programs.clearing_house.state.oracle import *
from dataclasses import dataclass, field
#%%
import sys 
import driftpy
import copy 

from driftpy.math.amm import *
from driftpy.math.repeg import calculate_repeg_cost
from driftpy.math.funding import calculate_long_short_funding
from driftpy.math.trade import calculate_trade_slippage, calculate_target_price_trade, calculate_trade_acquired_amounts
from driftpy.math.positions import calculate_base_asset_value, calculate_position_pnl, calculate_position_funding_pnl
from driftpy.types import PositionDirection, AssetType, MarketPosition, SwapDirection
from driftpy.math.market import calculate_mark_price, calculate_bid_price, calculate_ask_price
from driftpy.math.user import *

from driftpy.constants.numeric_constants import * 
from programs.clearing_house.controller.amm import calculate_quote_swap_output_with_spread,calculate_base_swap_output_with_spread
from programs.clearing_house.math.amm import update_mark_price_std, update_intensity

from solana.publickey import PublicKey

import json 
import matplotlib.pyplot as plt 
import numpy as np 
import pandas as pd
from dataclasses import dataclass, field

@dataclass
class AMM:
    oracle: Oracle 
    
    # constant product 
    base_asset_reserve: float  = 0 
    quote_asset_reserve: float  = 0
    funding_period: int = 3600
    
    sqrt_k: float = 0 
    peg_multiplier: int = 0 
    
    # liquidity providing 
    cumulative_funding_payment_per_lp: int = 0 
    cumulative_fee_per_lp: int = 0 
    cumulative_net_base_asset_amount_per_lp: int = 0 
    total_lp_shares: int = 0
    amm_lp_shares: int = 0

    # lp_net_baa: int = 0 
    # taker_net_baa: int = 0 
    lp_fee_payment: int = 0
    upnl: int = 0 
    
    # funding rates 
    last_funding_rate: int = 0
    last_funding_rate_ts: int = 0
        
    cumulative_funding_rate_long: int = 0 
    cumulative_funding_rate_short: int = 0 

    # twaps 
    last_oracle_price: int = 0
    last_oracle_conf: int = 0
    last_oracle_normalised_price: int = 0

    last_oracle_price_twap: int = 0
    last_oracle_price_twap_ts: int = 0

    last_mark_price: int = 0
    last_mark_price_twap: int = 0
    last_bid_price_twap: int = 0
    last_ask_price_twap: int = 0
    last_mark_price_twap_ts: int = 0

    # market making
    net_base_asset_amount: int = 0 # net user position
    base_spread: int = 0
    mark_std: int = 0
    buy_intensity: int = 0
    sell_intensity: int = 0

    last_spread: int = 0
    bid_price_before: int = 0
    ask_price_before: int = 0

    # formulaic peg
    total_fee: int = 0
    total_fee_minus_distributions: int = 0

    strategies: str = ''
    
    minimum_quote_asset_trade_size: int = 10_000_000
    minimum_base_asset_trade_size: int = 10_000_000

    quote_asset_amount_long: int = 0
    quote_asset_amount_short: int = 0
    terminal_quote_asset_reserve: int = 0


    # order filling

    # last_taker_mark_price_before: int = 0
    # last_taker_mark_price_after: int = 0

    def __post_init__(self):
        # self.peg_multiplier = PEG_PRECISION 
        now = 0
        
        oracle_price = self.oracle.get_price(now)
        self.last_oracle_price = oracle_price
        self.last_oracle_normalised_price = oracle_price

        self.last_oracle_price_twap = oracle_price
        self.last_oracle_price_twap_ts = now 
        
        mark_price = calculate_price(
            self.base_asset_reserve, 
            self.quote_asset_reserve, 
            self.peg_multiplier
        )
        
        if self.base_asset_reserve != self.quote_asset_reserve:
            self.sqrt_k = int((
                self.base_asset_reserve/1e13 * self.quote_asset_reserve/1e13
            ) ** .5) * 1e13
        else:
            self.sqrt_k = self.base_asset_reserve
        
        self.total_lp_shares = self.sqrt_k
        self.amm_lp_shares = self.total_lp_shares # amm has it all at once
        
        # # TODO 1 token per sqrt k 
        # reserves_in_quote = self.quote_asset_reserve / 1e13 * QUOTE_PRECISION
        # self.lp_tokens = reserves_in_quote
        # self.total_lp_tokens = reserves_in_quote
        # self.total_lp_value = reserves_in_quote
        
        self.bid_price_before = calculate_bid_price_amm(self, oracle_price)
        self.ask_price_before = calculate_ask_price_amm(self, oracle_price)
        self.last_ask_price_twap = mark_price
        self.last_bid_price_twap = mark_price
        self.last_mark_price_twap = mark_price
        self.last_mark_price_twap_ts = now 
        
        self.cumulative_funding_rate_long = 0 
        self.cumulative_funding_rate_short = 0 
        self.last_funding_rate_ts = now
        self.mark_std = 0
        self.terminal_quote_asset_reserve = self.quote_asset_reserve

@dataclass
class Market: 
    amm: AMM 
    market_index: int = 0
    
    # TODO: fix typing/name scheme here to match types.py
    base_asset_amount_long: int = 0
    base_asset_amount_short: int = 0 

    base_asset_amount: int = 0
    total_base_asset_amount: int = 0

    open_interest: int = 0
    total_exchange_fees: int = 0 
    total_mm_fees: int = 0 

    margin_ratio_initial: int = 1000
    margin_ratio_maintenance: int = 625 
    margin_ratio_partial: int = 500
    
    def to_json(self, now):
        # current prices 
        mark_price = calculate_mark_price(self)
        oracle_price = self.amm.oracle.get_price(now)
        
        market_dict = copy.deepcopy(self.__dict__)
        market_dict.pop("amm")
        
        amm_dict = copy.deepcopy(self.amm.__dict__)
        amm_dict.pop("oracle")
        b1 = amm_dict['base_asset_reserve']
        q1 = amm_dict['quote_asset_reserve']
        amm_dict['base_asset_reserve'] = f'{b1:.0f}'
        amm_dict['quote_asset_reserve'] = f'{q1:.0f}'

        mark_price = calculate_mark_price(self, oracle_price)
        bid_price = calculate_bid_price(self, oracle_price)
        ask_price = calculate_ask_price(self, oracle_price)
        peg = calculate_peg_multiplier(self.amm, oracle_price)
        wouldbe_peg_cost = calculate_repeg_cost(self, peg)[0]
        
        long_funding, short_funding = calculate_long_short_funding(self)
        predicted_long_funding = long_funding
        predicted_short_funding = short_funding
        last_mid_price_twap = (amm_dict['last_bid_price_twap']+amm_dict['last_ask_price_twap'])/2
        repeg_to_oracle_cost = calculate_repeg_cost(self, int(oracle_price * 1e3))[0]
                    
        # all in one 
        data = dict(
            mark_price=mark_price, 
            oracle_price=oracle_price,
            bid_price=bid_price, 
            ask_price=ask_price, 
            wouldbe_peg=peg/1e3, 
            wouldbe_peg_cost=wouldbe_peg_cost, 
            predicted_long_funding=predicted_long_funding,
            predicted_short_funding=predicted_short_funding,
            last_mid_price_twap=last_mid_price_twap,
            repeg_to_oracle_cost=repeg_to_oracle_cost
        ) | market_dict | amm_dict
        
        # rescale 
        for key in ['total_fee', 'total_mm_fees', 'total_exchange_fees', 'total_fee_minus_distributions']:
            data[key] /= 1e6
        
        return data 
       
