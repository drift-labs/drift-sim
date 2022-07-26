from programs.clearing_house.state import User, SimulationMarket
from programs.clearing_house.math.lp import get_lp_metrics
from programs.clearing_house.helpers import max_collateral_change

## converts the current virtual lp position into a real position 
## without burning lp tokens 
def settle_lp_shares(
    user: User, 
    market: SimulationMarket, 
    lp_token_amount: int, 
):
    position = user.positions[market.market_index]
    lp_metrics = get_lp_metrics(position, lp_token_amount, market)
    
    # print('--- lp settle ---')
    # print(f"metrics :: lp{position.user_index} (baa qaa):", lp_metrics.base_asset_amount, lp_metrics.quote_asset_amount / 1e6)
    # print(f"lp{position.user_index} funding payment:", lp_metrics.funding_payment)
    # print(f"lp{position.user_index} fee payment:", lp_metrics.fee_payment)

    # update market position 
    is_new_position = position.lp_base_asset_amount == 0 
    is_increase = position.lp_base_asset_amount > 0 and lp_metrics.base_asset_amount > 0 \
        or position.lp_base_asset_amount < 0 and lp_metrics.base_asset_amount < 0

    if is_increase or is_new_position:
        position.lp_base_asset_amount += lp_metrics.base_asset_amount
        position.lp_quote_asset_amount += lp_metrics.quote_asset_amount

    elif lp_metrics.base_asset_amount != 0: # is reduce/close
        net_qaa = abs(lp_metrics.quote_asset_amount - position.lp_quote_asset_amount)
        net_baa = lp_metrics.base_asset_amount + position.lp_base_asset_amount 

        position.lp_base_asset_amount = net_baa
        position.lp_quote_asset_amount = net_qaa

    # payments 
    lp_payment = lp_metrics.fee_payment + lp_metrics.unsettled_pnl + lp_metrics.funding_payment
    position.lp_funding_payments += lp_metrics.funding_payment
    position.lp_fee_payments += lp_metrics.fee_payment

    lp_payment = max_collateral_change(user, lp_payment)
    user.collateral += lp_payment
    
    assert lp_metrics.unsettled_pnl <= 0, 'shouldnt happen'
    market.amm.upnl -= lp_metrics.unsettled_pnl

    # update stats 
    position.last_cumulative_funding_rate_lp = market.amm.cumulative_funding_payment_per_lp
    position.last_cumulative_fee_per_lp = market.amm.cumulative_fee_per_lp
    position.last_cumulative_net_base_asset_amount_per_lp = market.amm.cumulative_net_base_asset_amount_per_lp

    return lp_metrics