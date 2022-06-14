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
from programs.clearing_house.controller.amm import calculate_quote_swap_output_with_spread,calculate_base_swap_output_with_spread
from programs.clearing_house.math.amm import update_mark_price_std, update_intensity

from solana.publickey import PublicKey

import json 
import matplotlib.pyplot as plt 
import numpy as np 
import pandas as pd
from dataclasses import dataclass, field

from programs.clearing_house.state import *

@dataclass
class MarketPosition: 
    market_index: int = 0
    base_asset_amount: int = 0
    quote_asset_amount: int = 0
    last_cumulative_funding_rate: int = 0
    last_funding_rate_ts: int = 0
    
@dataclass
class LPPosition: 
    market_index: int = 0
    lp_tokens: int = 0
    last_cumulative_lp_funding: int = 0
    last_net_position: int = 0
    last_fee_amount: int = 0
    last_quote_asset_reserve_amount: int = 0
    
@dataclass
class User:
    collateral: int
    locked_collateral: int = 0
    
    positions: list[MarketPosition] = field(default_factory=list)
    lp_positions: list[LPPosition] = field(default_factory=list)
    
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
                
                position_pnl = calculate_position_pnl(market, position)
                position_data['upnl'] = position_pnl
                position_data['ufunding'] = calculate_position_funding_pnl(market, position)
                
                total_pnl += position_pnl
                
                add_prefix(position_data, name)        
                data = data | position_data
        
        for lp_position in self.lp_positions:
            if lp_position.lp_tokens != 0: 
                name = f"m{lp_position.market_index}"
                position_data = copy.deepcopy(lp_position.__dict__)
                position_data.pop("market_index")
                
                # TODO: serialize more data -- basically do what the liquidator would do 
                
                add_prefix(position_data, name)
                data = data | position_data
        
        data["total_collateral"] = data["collateral"] + total_pnl
        
        return data

# todo: dont duplicate this code 
def add_prefix(data: dict, prefix: str):
    for key in list(data.keys()): 
        data[f"{prefix}_{key}"] = data.pop(key)

