from dataclasses import dataclass

@dataclass
class LPMetrics:
    fee_payment: int = 0
    funding_payment: int = 0 
    unsettled_pnl: int = 0 
    base_asset_amount: int = 0 
    quote_asset_amount: int = 0 