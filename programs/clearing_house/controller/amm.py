#%%
import sys

from construct import Short 
import driftpy

from driftpy.math.amm import (
    calculate_swap_output, 
    calculate_amm_reserves_after_swap, 
    get_swap_direction, 
    calculate_price,
    calculate_spread_reserves
)
from driftpy.math.trade import calculate_trade_slippage, calculate_target_price_trade, calculate_trade_acquired_amounts
from driftpy.math.positions import calculate_base_asset_value, calculate_position_pnl
from driftpy.types import AMM, PositionDirection, MarketPosition, SwapDirection
from driftpy.math.market import calculate_mark_price

from driftpy.constants.numeric_constants import * 

from solana.publickey import PublicKey

import json 
import matplotlib.pyplot as plt 
import numpy as np 
import pandas as pd
from dataclasses import dataclass, field

from programs.clearing_house.math.quote_asset import asset_to_reserve_amount, reserve_to_asset_amount
from programs.clearing_house.math.amm import calculate_quote_asset_amount_swapped, update_mark_twap
from programs.clearing_house.state.market import SimulationAMM


def swap_quote_asset(
    amm, 
    base_amount, 
    swap_direction, 
    now,
    use_spread=False,
):
    update_mark_twap(amm, now)

    oracle_price = amm.oracle.get_price(now)

    if use_spread:
        (new_base_asset_amount,
        new_quote_asset_amount,
        base_asset_acquired,
        quote_asset_amount_surplus) =  calculate_quote_swap_output_with_spread(amm, base_amount, swap_direction, oracle_price)
    else:
        #todo: _quote_asset_amount_surplus
        (new_base_asset_amount,
        new_quote_asset_amount,
        base_asset_acquired) =  _swap_quote_asset(amm, base_amount, swap_direction)
        quote_asset_amount_surplus = 0

    # update market
    amm.quote_asset_reserve = new_quote_asset_amount
    amm.base_asset_reserve = new_base_asset_amount

    return base_asset_acquired, quote_asset_amount_surplus

def _swap_quote_asset(
    amm, 
    quote_amount, 
    swap_direction, 
):    
    initial_base_asset_amount = amm.base_asset_reserve
    
    # compute swap output 
    """
    amm, input_asset_type: AssetType, swap_amount, swap_direction: SwapDirection
    """
    new_quote_asset_amount, new_base_asset_amount = driftpy.math.amm.calculate_amm_reserves_after_swap(
        amm, 
        driftpy.math.amm.AssetType.QUOTE,
        quote_amount, 
        swap_direction,
    )
    base_amount_acquired = initial_base_asset_amount - new_base_asset_amount
    
    return new_base_asset_amount, new_quote_asset_amount, base_amount_acquired

def swap_base_asset(
    amm, 
    base_amount, 
    swap_direction, 
    now,
    use_spread=False, 
):
    update_mark_twap(amm, now)

    if use_spread:
        (new_base_asset_amount,
        new_quote_asset_amount,
        quote_asset_acquired,
        quote_asset_amount_surplus) =  calculate_base_swap_output_with_spread(amm, base_amount, swap_direction)
    else:
        (new_base_asset_amount,
        new_quote_asset_amount,
        quote_asset_acquired) =  _swap_base_asset(amm, base_amount, swap_direction)
        quote_asset_amount_surplus = 0
            
    # update market
    amm.quote_asset_reserve = new_quote_asset_amount
    amm.base_asset_reserve = new_base_asset_amount

    return quote_asset_acquired, quote_asset_amount_surplus

def _swap_base_asset(
    amm: SimulationAMM, 
    base_amount, 
    swap_direction, 
):
    initial_quote_asset_reserve = amm.quote_asset_reserve
    
    # compute swap output 
    [new_quote_asset_amount, new_base_asset_amount] = driftpy.math.positions.calculate_amm_reserves_after_swap(
        amm, 
        driftpy.math.amm.AssetType.BASE,
        abs(base_amount), 
        swap_direction,
    )
    
    # remove = go long by removing base asset from pool 
    quote_reserve_change = {
        SwapDirection.ADD: initial_quote_asset_reserve - new_quote_asset_amount,
        SwapDirection.REMOVE: new_quote_asset_amount - initial_quote_asset_reserve,
    }[swap_direction]
    
    # reserves to quote amount 
    quote_amount_acquired = (
        quote_reserve_change 
        * amm.peg_multiplier 
        / AMM_TIMES_PEG_TO_QUOTE_PRECISION_RATIO
    )
    
    if swap_direction == driftpy.math.amm.SwapDirection.REMOVE:
        quote_amount_acquired += 1
    
    return new_base_asset_amount, new_quote_asset_amount, quote_amount_acquired


def calculate_quote_swap_output_with_spread(
    amm: SimulationAMM,
    quote_asset_amount: int,
    direction: SwapDirection,
    oracle_price=None
 ):
    quote_asset_reserve_amount = asset_to_reserve_amount(quote_asset_amount, amm.peg_multiplier)


    position_direction = PositionDirection.LONG if direction == SwapDirection.ADD else PositionDirection.SHORT
    base_asset_reserve_with_spread, quote_asset_reserve_with_spread = calculate_spread_reserves(
        amm,
        position_direction,
        oracle_price
    )

    # print('calculate_swap_output', quote_asset_reserve_amount, quote_asset_reserve_with_spread)
    
    new_base_asset_reserve_with_spread, _ = calculate_swap_output(
        quote_asset_reserve_amount, 
        quote_asset_reserve_with_spread, 
        direction,
        amm.sqrt_k,
    )

    base_asset_amount_with_spread = base_asset_reserve_with_spread - new_base_asset_reserve_with_spread

    # second do the swap based on normal reserves to get updated reserves
    new_base_asset_reserve, new_quote_asset_reserve = calculate_swap_output(
        quote_asset_reserve_amount,
        amm.quote_asset_reserve,
        direction,
        amm.sqrt_k,
    )

    quote_asset_reserve_if_closed, _ = calculate_swap_output(
        abs(base_asset_amount_with_spread),
        new_base_asset_reserve,
        direction,
        amm.sqrt_k,
    )

    quote_asset_amount_surplus = calculate_quote_asset_amount_surplus( new_quote_asset_reserve,
        quote_asset_reserve_if_closed,
        direction,
        amm.peg_multiplier,
        quote_asset_amount,
        False)

    return [new_base_asset_reserve,
        new_quote_asset_reserve,
        base_asset_amount_with_spread,
        quote_asset_amount_surplus]

def calculate_base_swap_output_with_spread(
    amm: SimulationAMM,
    base_asset_swap_amount: int,
    direction: SwapDirection,
 ):
    position_direction = PositionDirection.SHORT if direction == SwapDirection.ADD else PositionDirection.LONG
    base_asset_reserve_with_spread, quote_asset_reserve_with_spread = calculate_spread_reserves(
        amm,
        position_direction
    )

    new_quote_asset_reserve_with_spread, _ = calculate_swap_output(
        abs(base_asset_swap_amount), 
        base_asset_reserve_with_spread, 
        direction,
        amm.sqrt_k
    )

    quote_asset_amount = calculate_quote_asset_amount_swapped(quote_asset_reserve_with_spread,
     new_quote_asset_reserve_with_spread,
          direction,
        amm.peg_multiplier)


    # second do the swap based on normal reserves to get updated reserves
    new_quote_asset_reserve, new_base_asset_reserve = calculate_swap_output(
        abs(base_asset_swap_amount),
        amm.base_asset_reserve,
        direction,
        amm.sqrt_k,
    )

    # _, quote_asset_reserve_if_closed = calculate_swap_output(
    #     abs(base_asset_amount_with_spread),
    #     new_base_asset_reserve,
    #     direction,
    #     amm.sqrt_k,
    # )

    opposite_direction = SwapDirection.ADD if direction == SwapDirection.REMOVE else SwapDirection.REMOVE

    quote_asset_amount_surplus = calculate_quote_asset_amount_surplus( 
        new_quote_asset_reserve,
         amm.quote_asset_reserve,
        opposite_direction,
        amm.peg_multiplier,
        quote_asset_amount,
        direction == SwapDirection.REMOVE)

    return [new_base_asset_reserve,
        new_quote_asset_reserve,
        quote_asset_amount,
        quote_asset_amount_surplus]


def calculate_quote_asset_amount_surplus(
    quote_asset_reserve_before: int,
    quote_asset_reserve_after: int,
    swap_direction: SwapDirection,
    peg_multiplier: int,
    initial_quote_asset_amount: int,
    round_down: bool):

    if swap_direction == SwapDirection.ADD:
        # try:
        quote_asset_reserve_change = quote_asset_reserve_before - quote_asset_reserve_after
        # except:
        #     print('FAILED', quote_asset_reserve_before, quote_asset_reserve_after)
    else:
        quote_asset_reserve_change = quote_asset_reserve_after - quote_asset_reserve_before

    actual_quote_asset_amount = reserve_to_asset_amount(quote_asset_reserve_change, peg_multiplier)

    # Compensate for +1 quote asset amount added when removing base asset
    if round_down:
        actual_quote_asset_amount += 1

    if actual_quote_asset_amount > initial_quote_asset_amount:
        quote_asset_amount_surplus = actual_quote_asset_amount - initial_quote_asset_amount
    else:
        quote_asset_amount_surplus = initial_quote_asset_amount - actual_quote_asset_amount

    return quote_asset_amount_surplus


def move_to_price(amm: SimulationAMM, target_price: int):

    k = amm.sqrt_k*amm.sqrt_k

    new_base_asset_amount_squared = (k * amm.peg_multiplier * PRICE_TO_PEG_PRECISION_RATIO)/target_price
    new_base_asset_amount = np.sqrt(new_base_asset_amount_squared)
    new_quote_asset_amount = k/new_base_asset_amount
    
    amm.base_asset_reserve = new_base_asset_amount
    amm.quote_asset_reserve = new_quote_asset_amount
