from programs.clearing_house.state import SimulationMarket, MarketPosition, LPMetrics
from programs.clearing_house.controller.amm import calculate_base_swap_output_with_spread 

from driftpy.constants.numeric_constants import * 
from driftpy.math.amm import (
    calculate_swap_output, 
)
from driftpy.types import SwapDirection

def get_lp_metrics(
    position: MarketPosition, 
    lp_shares_to_settle: int, 
    market: SimulationMarket
) -> LPMetrics: 
    lp_token_amount = lp_shares_to_settle

    # give them portion of fees since deposit 
    change_in_fees = market.amm.cumulative_fee_per_lp - position.last_cumulative_fee_per_lp
    assert change_in_fees >= 0, f"lp loses money: {market.amm.cumulative_fee_per_lp} {position.last_cumulative_fee_per_lp}"
    fee_payment = change_in_fees * lp_token_amount / 1e13

    # give them portion of funding since deposit
    change_in_funding = (
        market.amm.cumulative_funding_payment_per_lp   
        - position.last_cumulative_funding_rate_lp
    ) # in quote 
    change_in_funding *= -1 # consistent with settle_funding         
    funding_payment = change_in_funding * lp_token_amount / 1e13

    # give them the amm position  
    # print(
    #     "lp settling (last, curr):", 
    #     position.last_cumulative_base_asset_amount_with_amm_per_lp,
    #     market.amm.cumulative_base_asset_amount_with_amm_per_lp
    # )

    amm_net_position_change = (
        position.last_cumulative_base_asset_amount_with_amm_per_lp -
        market.amm.cumulative_base_asset_amount_with_amm_per_lp
    ) * market.amm.total_lp_shares

    market_baa = 0 
    market_qaa = 0 
    unsettled_pnl = 0 

    if amm_net_position_change != 0: 
        direction_to_close = {
            True: SwapDirection.REMOVE,
            False: SwapDirection.ADD,
        }[amm_net_position_change > 0]

        if market.amm.base_spread == 0: 
            new_quote_asset_reserve, _ = calculate_swap_output(
                abs(amm_net_position_change), 
                market.amm.base_asset_reserve,
                direction_to_close,
                market.amm.sqrt_k
            )
        else: 
            new_quote_asset_reserve = calculate_base_swap_output_with_spread(
                market.amm, abs(amm_net_position_change), direction_to_close
            )[1]

        base_asset_amount = (
            amm_net_position_change
            * lp_token_amount 
            / market.amm.total_lp_shares
        )

        # someone goes long => amm_quote_position_change > 0
        amm_quote_position_change = (
            new_quote_asset_reserve -
            market.amm.quote_asset_reserve
        ) 

        # amm_quote_position_change > 0 then we need to increase cost basis 
        # position.quote_asset_amount is used for PnL 
        quote_asset_amount = int(
            amm_quote_position_change
            * lp_token_amount 
            / market.amm.total_lp_shares
        ) * market.amm.peg_multiplier / AMM_TIMES_PEG_TO_QUOTE_PRECISION_RATIO
        quote_asset_amount = abs(quote_asset_amount)
        
        min_baa = market.amm.base_asset_amount_step_size
        min_qaa = market.amm.minimum_quote_asset_trade_size

        if abs(base_asset_amount) > min_baa and quote_asset_amount > min_qaa: 
            market_baa = base_asset_amount
            market_qaa = quote_asset_amount
        else:
            print('warning market position to small')
            print(f"{base_asset_amount} {min_baa} : {quote_asset_amount} {min_qaa}")
            tsize = market.amm.minimum_quote_asset_trade_size
            unsettled_pnl = -tsize
        
    lp_metrics = LPMetrics(
        base_asset_amount=market_baa, 
        quote_asset_amount=market_qaa, 
        fee_payment=fee_payment, 
        funding_payment=funding_payment, 
        unsettled_pnl=unsettled_pnl
    )

    return lp_metrics
