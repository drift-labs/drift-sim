from dataclasses import dataclass, field
#%%
import sys 
import driftpy
import copy 

from driftpy.math.amm import (
    calculate_swap_output, 
    calculate_amm_reserves_after_swap, 
    get_swap_direction, 
    calculate_price
)
from driftpy.math.trade import calculate_trade_slippage, calculate_target_price_trade, calculate_trade_acquired_amounts
from driftpy.math.positions import calculate_base_asset_value, calculate_position_pnl, calculate_position_funding_pnl
from driftpy.types import PositionDirection, AssetType, MarketPosition, SwapDirection
from driftpy.math.market import calculate_mark_price, calculate_bid_price, calculate_ask_price
from driftpy.math.amm import calculate_mark_price_amm, calculate_bid_price_amm, calculate_ask_price_amm

from driftpy.math.user import *

from driftpy.constants.numeric_constants import * 

from solana.publickey import PublicKey

import json 
import matplotlib.pyplot as plt 
import numpy as np 
import pandas as pd
from dataclasses import dataclass, field

from programs.clearing_house.state import *

@dataclass
class LPMetrics:
    fee_payment: int = 0
    funding_payment: int = 0 
    unsettled_pnl: int = 0 
    base_asset_amount: int = 0 
    quote_asset_amount: int = 0 
    
@dataclass
class MarketPosition: 
    user_index: int
    market_index: int = 0
    base_asset_amount: int = 0
    quote_asset_amount: int = 0
    last_cumulative_funding_rate: int = 0
    last_funding_rate_ts: int = 0

    # lp stuff
    lp_shares: int = 0
    lp_base_asset_amount: int = 0 
    lp_quote_asset_amount: int = 0 
    last_cumulative_funding_rate_lp: int = 0
    last_cumulative_fee_per_lp: int = 0 
    last_cumulative_net_base_asset_amount_per_lp: int = 0 

    # other metrics for debugging
    lp_funding_payments: int = 0 
    lp_fee_payments: int = 0 
    market_fee_payments: int = 0 
    market_funding_payments: int = 0
    total_baa: int = 0 
    
@dataclass
class User:
    user_index: int
    collateral: int
    
    positions: list[MarketPosition] = field(default_factory=list)
    
    total_fee_paid: int = 0 
    total_fee_rebate: int = 0
    open_orders: int = 0 
    cumulative_deposits: int = 0 
    
    def to_json(self, clearing_house):
        markets = clearing_house.markets
        data = dict(
            collateral=self.collateral,
            free_collateral=get_free_collateral(self, markets),
            margin_ratio=get_margin_ratio(self, markets),
            total_position_value=get_total_position_value(self.positions, markets),
            total_fee_paid=self.total_fee_paid,
            total_fee_rebate=self.total_fee_rebate,
            open_orders=self.open_orders,
            cumulative_deposits=self.cumulative_deposits,
        )
        
        total_pnl = 0 
        for position in self.positions:
            if position.base_asset_amount != 0: 
                name = f"m{position.market_index}"
                position_data = copy.deepcopy(position.__dict__)
                position_data.pop("market_index")
                
                market = clearing_house.markets[position.market_index]
                mark = calculate_mark_price(market)
                position_pnl = calculate_position_pnl(market, position)
                position_data['upnl'] = position_pnl
                
                if position.base_asset_amount > 0:
                    upnl_noslip = mark*position.base_asset_amount/1e13 - position.quote_asset_amount
                else:
                    upnl_noslip = position.quote_asset_amount - mark*position.base_asset_amount/1e13

                position_data['upnl_noslip'] = upnl_noslip
                position_data['ufunding'] = calculate_position_funding_pnl(market, position)
                
                total_pnl += position_pnl
                
                add_prefix(position_data, name)        
                data = data | position_data
        
        data["total_collateral"] = data["collateral"] + total_pnl
        
        return data

# todo: dont duplicate this code 
def add_prefix(data: dict, prefix: str):
    for key in list(data.keys()): 
        data[f"{prefix}_{key}"] = data.pop(key)

