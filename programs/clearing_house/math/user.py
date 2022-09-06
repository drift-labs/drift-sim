
from driftpy.types import PositionDirection, MarketPosition, SwapDirection, User, AMM
from programs.clearing_house.math.stats import calculate_rolling_average

THRITY_DAYS = 60*60*24*30

def update_quote_volume_30d(
    user: User,
    now: int,
    quote_asset_amount: int,
):
    # calculate EWM-sum of user's volume within drift protocol
    # rolling sum of 30d volume  ~=
    # ((30days - since_last)/30days) * quote_volume_30d + new trade volume
    user_last_trade_ts = now - 30 #todo
    user_rolling_volume = 0
    since_last = now - user_last_trade_ts
    new_rolling_volume = calculate_rolling_average(user_rolling_volume, quote_asset_amount, since_last, THRITY_DAYS)

