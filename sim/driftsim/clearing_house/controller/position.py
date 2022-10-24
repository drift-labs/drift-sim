from sim.driftsim.clearing_house.state import MarketPosition, SimulationMarket

def track_new_base_assset(
    position: MarketPosition, 
    market: SimulationMarket, 
    base_amount_acquired: int, 
    quote_amount: int, 
    is_lp_update: bool = False, 
):
    is_long_reduce = position.base_asset_amount > 0 and base_amount_acquired < 0
    is_short_reduce = position.base_asset_amount < 0 and base_amount_acquired > 0
    is_reduce = is_long_reduce or is_short_reduce
    abs_acquired = abs(base_amount_acquired) 
    abs_current_baa = abs(position.base_asset_amount)
    is_flip = (is_long_reduce and abs_acquired > abs_current_baa) or (is_short_reduce and abs_acquired > abs_current_baa) 
    is_new_position = position.base_asset_amount == 0 and base_amount_acquired != 0
    is_close = position.base_asset_amount + base_amount_acquired == 0 and position.base_asset_amount != 0
    
    if base_amount_acquired == 0 and quote_amount == 0: 
        return 

    # the flippening
    assert not is_flip, "trying to update a position flip" 

    if is_reduce or is_close:
        assert quote_amount < 0

    # update market 
    if (is_new_position and base_amount_acquired > 0) or position.base_asset_amount > 0:
        market.amm.base_asset_amount_long += base_amount_acquired
        market.amm.quote_asset_amount_long += quote_amount
    elif (is_new_position and base_amount_acquired < 0) or position.base_asset_amount < 0:
        market.amm.base_asset_amount_short += base_amount_acquired 
        market.amm.quote_asset_amount_short += quote_amount
    else: 
        assert False, 'shouldnt be called...'

    market.amm.base_asset_amount_with_amm += base_amount_acquired

    if not is_lp_update: 
        # need to update this like a normal position
        market.amm.cumulative_base_asset_amount_with_amm_per_lp += base_amount_acquired / market.amm.total_lp_shares
        # market.amm.cumulative_net_quote_asset_amount_per_lp += quote_amount / market.amm.total_lp_shares

    if is_new_position: 
        # update the funding rate if new position 
        position.last_cumulative_funding_rate = {
            True: market.amm.cumulative_funding_rate_long,
            False: market.amm.cumulative_funding_rate_short
        }[position.base_asset_amount > 0]
        market.number_of_users += 1 

    if is_close:
        market.number_of_users -= 1 

    position.base_asset_amount += base_amount_acquired
    position.quote_asset_amount += quote_amount