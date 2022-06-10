
from driftpy.math.trade import calculate_trade_slippage, calculate_target_price_trade, calculate_trade_acquired_amounts
from driftpy.math.positions import calculate_base_asset_value, calculate_position_pnl
from driftpy.types import PositionDirection, AssetType, MarketPosition, SwapDirection, User, AMM
from driftpy.math.market import calculate_mark_price
from programs.clearing_house.math.quote_asset import *
from programs.clearing_house.math.stats import calculate_rolling_average
from driftpy.math.amm import calculate_mark_price_amm, calculate_bid_price_amm, calculate_ask_price_amm

ONE_HOUR = 60*60
ONE_MIN = 60

def calculate_quote_asset_amount_swapped(quote_asset_reserve_before:int, 
quote_asset_reserve_after:int, 
swap_direction: SwapDirection,
peg_multiplier: int
):
    if swap_direction == SwapDirection.ADD:
        quote_asset_reserve_change = quote_asset_reserve_before - quote_asset_reserve_after
    else:
        quote_asset_reserve_change = quote_asset_reserve_after - quote_asset_reserve_before


    quote_asset_amount = reserve_to_asset_amount(quote_asset_reserve_change, peg_multiplier)

    if swap_direction == SwapDirection.REMOVE:
        quote_asset_amount+=1
    
    return quote_asset_amount

def update_mark_price_std(
    amm: AMM,
    now: int,
    price_change: int,
):
    # calculate EWM-sum of user's volume within drift protocol
    # rolling sum of k-peroid volume  ~=
    # ((30days - since_last)/30days) * quote_volume_30d + new trade volume

    since_last = now - amm.last_mark_price_twap_ts
    last_mark_price_std = amm.mark_std
    new_mark_price_std = calculate_rolling_average(last_mark_price_std, abs(price_change), since_last, ONE_MIN*60)
    amm.mark_std = new_mark_price_std

def update_intensity(
    amm: AMM,
    now: int,
    quote_asset_amount: int,
    direction: PositionDirection
):
    # calculate EWM-sum of user's volume within drift protocol
    # rolling sum of k-peroid volume  ~=
    # ((30days - since_last)/30days) * quote_volume_30d + new trade volume


    since_last = now - amm.last_mark_price_ts
    
    new_buy_intensity = calculate_rolling_average(amm.last_buy_intensity, 
    abs(quote_asset_amount) if direction == PositionDirection.LONG else 0, 
    since_last, ONE_MIN)
    amm.last_buy_intensity = new_buy_intensity

    new_sell_intensity = calculate_rolling_average(amm.last_sell_intensity, 
    abs(quote_asset_amount) if direction == PositionDirection.SHORT else 0, 
    since_last, 
    ONE_MIN
    )

    amm.last_buy_intensity = new_buy_intensity
    amm.last_sell_intensity = new_sell_intensity


def calculate_new_twap(
    last_twap, 
    last_twap_ts, 
    current_value, 
    now, 
    funding_period
):
    since_last = max(1, now - last_twap_ts)
    from_start = max(1, funding_period - since_last)
    
    new_twap = calculate_weighted_average(
        current_value, 
        last_twap, 
        since_last, 
        from_start
    )
    return new_twap 

def update_oracle_twap(
    amm: AMM, 
    now: int          
):    
    new_oracle_twap = calculate_new_twap(
        amm.last_oracle_price_twap, 
        amm.last_oracle_price_twap_ts,  
        amm.last_oracle_price, 
        now, 
        amm.funding_period, 
    )

    amm.last_oracle_price = amm.oracle.get_price(now)
    amm.last_oracle_price_twap = new_oracle_twap
    amm.last_oracle_price_twap_ts = now 
    
    return new_oracle_twap

def update_mark_twap(
    amm: AMM, 
    now: int          
):
    mark_price = calculate_mark_price_amm(amm)
    
    new_mark_twap = calculate_new_twap(
        amm.last_mark_price_twap, 
        amm.last_mark_price_twap_ts, 
        mark_price, 
        now, 
        amm.funding_period, 
    )

    new_bid_twap = calculate_new_twap(
        amm.last_bid_price_twap, 
        amm.last_mark_price_twap_ts,  
        amm.bid_price_before, 
        now, 
        amm.funding_period, 
    )

    new_ask_twap = calculate_new_twap(
        amm.last_ask_price_twap, 
        amm.last_mark_price_twap_ts,  
        amm.ask_price_before, 
        now, 
        amm.funding_period, 
    )

    amm.last_mark_price_twap = new_mark_twap
    amm.last_bid_price_twap = new_bid_twap
    amm.last_ask_price_twap = new_ask_twap
    amm.last_mark_price_twap_ts = now 

    oracle_price = amm.oracle.get_price(now)
    amm.bid_price_before = calculate_bid_price_amm(amm, oracle_price) #* MARK_PRICE_PRECISION
    amm.ask_price_before = calculate_ask_price_amm(amm, oracle_price) #* MARK_PRICE_PRECISION

    
    return new_mark_twap
    
def calculate_weighted_average(
    data1, 
    data2, 
    weight1, 
    weight2
):
    denominator = weight1 + weight2
    prev_twap_99 = data1 * weight1
    latest_price_01 = data2 * weight2
    
    result = (
        (prev_twap_99 + latest_price_01) / denominator
    )
    return result
