from programs.clearing_house.state import User, Market, SimulationMarket
from programs.clearing_house.helpers import max_collateral_change

from driftpy.constants.numeric_constants import *

def settle_funding_rates(
    user: User, 
    markets: list[Market],
    now: int,
):
    total_funding_payment = 0 
    for position in user.positions: 
        market: SimulationMarket = [m for m in markets if m.market_index == position.market_index][0]

        if position.base_asset_amount == 0: 
            continue
        
        amm_cumulative_funding_rate = {
            True: market.amm.cumulative_funding_rate_long, 
            False: market.amm.cumulative_funding_rate_short
        }[position.base_asset_amount > 0]
        
        if position.last_cumulative_funding_rate != amm_cumulative_funding_rate:
            funding_delta = amm_cumulative_funding_rate - position.last_cumulative_funding_rate
            
            funding_payment = (
                funding_delta 
                * position.base_asset_amount
                / FUNDING_RATE_BUFFER 
                / AMM_TO_QUOTE_PRECISION_RATIO
            )
            
            # long @ f0 funding rate 
            # mark < oracle => funding_payment = mark - oracle < 0 => cum_funding decreases 
            # amm_cum < f0 [bc of decrease]
            # amm_cum - f0 < 0  :: long doesnt get paid in funding 
            # flip sign to make long get paid (not in v1 program? maybe doing something wrong)
            funding_payment = -funding_payment

            total_funding_payment += funding_payment 
            position.market_funding_payments += funding_payment
            
            position.last_cumulative_funding_rate = amm_cumulative_funding_rate
            position.last_funding_rate_ts = now 
            
    # dont pay more than the total number of fees 
    total_funding_payment = max_collateral_change(user, total_funding_payment)
    user.collateral += total_funding_payment
