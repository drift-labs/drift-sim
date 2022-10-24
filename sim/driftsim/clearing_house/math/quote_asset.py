from driftpy.constants.numeric_constants import AMM_TIMES_PEG_TO_QUOTE_PRECISION_RATIO, PRICE_PRECISION, PEG_PRECISION

def reserve_to_asset_amount(
    quote_asset_amount: int,
    peg_multiplier: int,
):
    return quote_asset_amount*peg_multiplier/AMM_TIMES_PEG_TO_QUOTE_PRECISION_RATIO

def asset_to_reserve_amount(
    quote_asset_amount: int,
    peg_multiplier: int,
):
    return quote_asset_amount*AMM_TIMES_PEG_TO_QUOTE_PRECISION_RATIO/peg_multiplier