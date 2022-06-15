#%%
import sys 
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

from solana.publickey import PublicKey

import json 
# import matplotlib.pyplot as plt 
import numpy as np 
import pandas as pd
from dataclasses import dataclass, field

from programs.clearing_house.state import Oracle, User
from programs.clearing_house.lib import ClearingHouse

@dataclass
class Event:     
    timestamp: int 
    
    def serialize_parameters(self):
        return json.loads(json.dumps(
                self, 
                default=lambda o: o.__dict__, 
                sort_keys=True, 
                indent=4
        ))
        
    def serialize_to_row(self):
        parameters = self.serialize_parameters()
        timestamp = parameters.pop("timestamp")
        event_name = parameters.pop("_event_name")
        row = {
            "event_name": event_name, 
            "timestamp": timestamp, 
            "parameters": json.dumps(parameters)
        }
        return row 
    
    @staticmethod
    def deserialize_from_row(class_type, event_row):
        event = json.loads(event_row.to_json())
        params = json.loads(event["parameters"])
        params["_event_name"] = event["event_name"]
        params["timestamp"] = event["timestamp"]
        event = class_type(**params)
        return event
    
    # this works for all Event subclasses
    @staticmethod
    def run_row(class_type, clearing_house: ClearingHouse, event_row) -> ClearingHouse:
        event = Event.deserialize_from_row(class_type, event_row)
        return event.run(clearing_house)
    
    def run(self, clearing_house: ClearingHouse) -> ClearingHouse:
        raise NotImplementedError
    
@dataclass
class NullEvent(Event):     
    _event_name: str = "null"
    
    def run(self, clearing_house: ClearingHouse) -> ClearingHouse:
        return clearing_house
    
@dataclass
class DepositCollateralEvent(Event): 
    user_index: int 
    deposit_amount: int
    username: str = "u"
    
    _event_name: str = "deposit_collateral"
    
    def run(self, clearing_house: ClearingHouse) -> ClearingHouse:
        clearing_house = clearing_house.deposit_user_collateral(
            self.user_index, 
            self.deposit_amount, 
            name=self.username
        )    
        return clearing_house
    
@dataclass 
class addLiquidityEvent(Event):
    market_index: int = 0 
    user_index: int = 0 
    quote_amount: int = 0 

    _event_name: str = "add_liquidity"

    def run(self, clearing_house: ClearingHouse) -> ClearingHouse:
        clearing_house = clearing_house.add_liquidity(
            self.market_index,
            self.user_index,
            self.quote_amount
        )
        return clearing_house


@dataclass
class removeLiquidityEvent(Event):
    market_index: int = 0 
    user_index: int = 0 
    lp_token_amount: int = 0 

    _event_name: str = "remove_liquidity"
    
    def run(self, clearing_house: ClearingHouse) -> ClearingHouse:
        clearing_house = clearing_house.remove_liquidity(
            self.market_index, 
            self.user_index, 
            self.lp_token_amount
        )
        
        return clearing_house
    
    
@dataclass
class OpenPositionEvent(Event): 
    user_index: int 
    direction: str 
    quote_amount: int 
    market_index: int
    
    _event_name: str = "open_position"
    
    def run(self, clearing_house: ClearingHouse) -> ClearingHouse:
        direction = {
            "long": PositionDirection.LONG,
            "short": PositionDirection.SHORT,
        }[self.direction]
        
        clearing_house = clearing_house.open_position(
            direction, 
            self.user_index, 
            self.quote_amount, 
            self.market_index
        )
        
        return clearing_house
                
