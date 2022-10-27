from __future__ import annotations
from . import (
    historical_oracle_data,
    pool_balance,
    oracle_source,
)
import typing
from dataclasses import dataclass
from construct import Container
from solana.publickey import PublicKey
from anchorpy.borsh_extension import BorshPubkey
import borsh_construct as borsh


class AMMJSON(typing.TypedDict):
    oracle: str
    historical_oracle_data: historical_oracle_data.HistoricalOracleDataJSON
    base_asset_amount_per_lp: int
    quote_asset_amount_per_lp: int
    fee_pool: pool_balance.PoolBalanceJSON
    base_asset_reserve: int
    quote_asset_reserve: int
    concentration_coef: int
    min_base_asset_reserve: int
    max_base_asset_reserve: int
    sqrt_k: int
    peg_multiplier: int
    terminal_quote_asset_reserve: int
    base_asset_amount_long: int
    base_asset_amount_short: int
    base_asset_amount_with_amm: int
    base_asset_amount_with_unsettled_lp: int
    max_open_interest: int
    quote_asset_amount_long: int
    quote_asset_amount_short: int
    quote_entry_amount_long: int
    quote_entry_amount_short: int
    user_lp_shares: int
    last_funding_rate: int
    last_funding_rate_long: int
    last_funding_rate_short: int
    last24h_avg_funding_rate: int
    total_fee: int
    total_mm_fee: int
    total_exchange_fee: int
    total_fee_minus_distributions: int
    total_fee_withdrawn: int
    total_liquidation_fee: int
    cumulative_funding_rate_long: int
    cumulative_funding_rate_short: int
    cumulative_social_loss: int
    ask_base_asset_reserve: int
    ask_quote_asset_reserve: int
    bid_base_asset_reserve: int
    bid_quote_asset_reserve: int
    last_oracle_normalised_price: int
    last_oracle_reserve_price_spread_pct: int
    last_bid_price_twap: int
    last_ask_price_twap: int
    last_mark_price_twap: int
    last_mark_price_twap5min: int
    last_update_slot: int
    last_oracle_conf_pct: int
    net_revenue_since_last_funding: int
    last_funding_rate_ts: int
    funding_period: int
    order_step_size: int
    order_tick_size: int
    min_order_size: int
    max_position_size: int
    volume24h: int
    long_intensity_volume: int
    short_intensity_volume: int
    last_trade_ts: int
    mark_std: int
    last_mark_price_twap_ts: int
    base_spread: int
    max_spread: int
    long_spread: int
    short_spread: int
    long_intensity_count: int
    short_intensity_count: int
    max_fill_reserve_fraction: int
    max_slippage_ratio: int
    curve_update_intensity: int
    amm_jit_intensity: int
    oracle_source: oracle_source.OracleSourceJSON
    last_oracle_valid: bool


@dataclass
class AMM:
    layout: typing.ClassVar = borsh.CStruct(
        "oracle" / BorshPubkey,
        "historical_oracle_data" / historical_oracle_data.HistoricalOracleData.layout,
        "base_asset_amount_per_lp" / borsh.I128,
        "quote_asset_amount_per_lp" / borsh.I128,
        "fee_pool" / pool_balance.PoolBalance.layout,
        "base_asset_reserve" / borsh.U128,
        "quote_asset_reserve" / borsh.U128,
        "concentration_coef" / borsh.U128,
        "min_base_asset_reserve" / borsh.U128,
        "max_base_asset_reserve" / borsh.U128,
        "sqrt_k" / borsh.U128,
        "peg_multiplier" / borsh.U128,
        "terminal_quote_asset_reserve" / borsh.U128,
        "base_asset_amount_long" / borsh.I128,
        "base_asset_amount_short" / borsh.I128,
        "base_asset_amount_with_amm" / borsh.I128,
        "base_asset_amount_with_unsettled_lp" / borsh.I128,
        "max_open_interest" / borsh.U128,
        "quote_asset_amount_long" / borsh.I128,
        "quote_asset_amount_short" / borsh.I128,
        "quote_entry_amount_long" / borsh.I128,
        "quote_entry_amount_short" / borsh.I128,
        "user_lp_shares" / borsh.U128,
        "last_funding_rate" / borsh.I64,
        "last_funding_rate_long" / borsh.I64,
        "last_funding_rate_short" / borsh.I64,
        "last24h_avg_funding_rate" / borsh.I64,
        "total_fee" / borsh.I128,
        "total_mm_fee" / borsh.I128,
        "total_exchange_fee" / borsh.U128,
        "total_fee_minus_distributions" / borsh.I128,
        "total_fee_withdrawn" / borsh.U128,
        "total_liquidation_fee" / borsh.U128,
        "cumulative_funding_rate_long" / borsh.I128,
        "cumulative_funding_rate_short" / borsh.I128,
        "cumulative_social_loss" / borsh.I128,
        "ask_base_asset_reserve" / borsh.U128,
        "ask_quote_asset_reserve" / borsh.U128,
        "bid_base_asset_reserve" / borsh.U128,
        "bid_quote_asset_reserve" / borsh.U128,
        "last_oracle_normalised_price" / borsh.I64,
        "last_oracle_reserve_price_spread_pct" / borsh.I64,
        "last_bid_price_twap" / borsh.U64,
        "last_ask_price_twap" / borsh.U64,
        "last_mark_price_twap" / borsh.U64,
        "last_mark_price_twap5min" / borsh.U64,
        "last_update_slot" / borsh.U64,
        "last_oracle_conf_pct" / borsh.U64,
        "net_revenue_since_last_funding" / borsh.I64,
        "last_funding_rate_ts" / borsh.I64,
        "funding_period" / borsh.I64,
        "order_step_size" / borsh.U64,
        "order_tick_size" / borsh.U64,
        "min_order_size" / borsh.U64,
        "max_position_size" / borsh.U64,
        "volume24h" / borsh.U64,
        "long_intensity_volume" / borsh.U64,
        "short_intensity_volume" / borsh.U64,
        "last_trade_ts" / borsh.I64,
        "mark_std" / borsh.U64,
        "last_mark_price_twap_ts" / borsh.I64,
        "base_spread" / borsh.U32,
        "max_spread" / borsh.U32,
        "long_spread" / borsh.U32,
        "short_spread" / borsh.U32,
        "long_intensity_count" / borsh.U32,
        "short_intensity_count" / borsh.U32,
        "max_fill_reserve_fraction" / borsh.U16,
        "max_slippage_ratio" / borsh.U16,
        "curve_update_intensity" / borsh.U8,
        "amm_jit_intensity" / borsh.U8,
        "oracle_source" / oracle_source.layout,
        "last_oracle_valid" / borsh.Bool,
    )
    oracle: PublicKey
    historical_oracle_data: historical_oracle_data.HistoricalOracleData
    base_asset_amount_per_lp: int
    quote_asset_amount_per_lp: int
    fee_pool: pool_balance.PoolBalance
    base_asset_reserve: int
    quote_asset_reserve: int
    concentration_coef: int
    min_base_asset_reserve: int
    max_base_asset_reserve: int
    sqrt_k: int
    peg_multiplier: int
    terminal_quote_asset_reserve: int
    base_asset_amount_long: int
    base_asset_amount_short: int
    base_asset_amount_with_amm: int
    base_asset_amount_with_unsettled_lp: int
    max_open_interest: int
    quote_asset_amount_long: int
    quote_asset_amount_short: int
    quote_entry_amount_long: int
    quote_entry_amount_short: int
    user_lp_shares: int
    last_funding_rate: int
    last_funding_rate_long: int
    last_funding_rate_short: int
    last24h_avg_funding_rate: int
    total_fee: int
    total_mm_fee: int
    total_exchange_fee: int
    total_fee_minus_distributions: int
    total_fee_withdrawn: int
    total_liquidation_fee: int
    cumulative_funding_rate_long: int
    cumulative_funding_rate_short: int
    cumulative_social_loss: int
    ask_base_asset_reserve: int
    ask_quote_asset_reserve: int
    bid_base_asset_reserve: int
    bid_quote_asset_reserve: int
    last_oracle_normalised_price: int
    last_oracle_reserve_price_spread_pct: int
    last_bid_price_twap: int
    last_ask_price_twap: int
    last_mark_price_twap: int
    last_mark_price_twap5min: int
    last_update_slot: int
    last_oracle_conf_pct: int
    net_revenue_since_last_funding: int
    last_funding_rate_ts: int
    funding_period: int
    order_step_size: int
    order_tick_size: int
    min_order_size: int
    max_position_size: int
    volume24h: int
    long_intensity_volume: int
    short_intensity_volume: int
    last_trade_ts: int
    mark_std: int
    last_mark_price_twap_ts: int
    base_spread: int
    max_spread: int
    long_spread: int
    short_spread: int
    long_intensity_count: int
    short_intensity_count: int
    max_fill_reserve_fraction: int
    max_slippage_ratio: int
    curve_update_intensity: int
    amm_jit_intensity: int
    oracle_source: oracle_source.OracleSourceKind
    last_oracle_valid: bool

    @classmethod
    def from_decoded(cls, obj: Container) -> "AMM":
        return cls(
            oracle=obj.oracle,
            historical_oracle_data=historical_oracle_data.HistoricalOracleData.from_decoded(
                obj.historical_oracle_data
            ),
            base_asset_amount_per_lp=obj.base_asset_amount_per_lp,
            quote_asset_amount_per_lp=obj.quote_asset_amount_per_lp,
            fee_pool=pool_balance.PoolBalance.from_decoded(obj.fee_pool),
            base_asset_reserve=obj.base_asset_reserve,
            quote_asset_reserve=obj.quote_asset_reserve,
            concentration_coef=obj.concentration_coef,
            min_base_asset_reserve=obj.min_base_asset_reserve,
            max_base_asset_reserve=obj.max_base_asset_reserve,
            sqrt_k=obj.sqrt_k,
            peg_multiplier=obj.peg_multiplier,
            terminal_quote_asset_reserve=obj.terminal_quote_asset_reserve,
            base_asset_amount_long=obj.base_asset_amount_long,
            base_asset_amount_short=obj.base_asset_amount_short,
            base_asset_amount_with_amm=obj.base_asset_amount_with_amm,
            base_asset_amount_with_unsettled_lp=obj.base_asset_amount_with_unsettled_lp,
            max_open_interest=obj.max_open_interest,
            quote_asset_amount_long=obj.quote_asset_amount_long,
            quote_asset_amount_short=obj.quote_asset_amount_short,
            quote_entry_amount_long=obj.quote_entry_amount_long,
            quote_entry_amount_short=obj.quote_entry_amount_short,
            user_lp_shares=obj.user_lp_shares,
            last_funding_rate=obj.last_funding_rate,
            last_funding_rate_long=obj.last_funding_rate_long,
            last_funding_rate_short=obj.last_funding_rate_short,
            last24h_avg_funding_rate=obj.last24h_avg_funding_rate,
            total_fee=obj.total_fee,
            total_mm_fee=obj.total_mm_fee,
            total_exchange_fee=obj.total_exchange_fee,
            total_fee_minus_distributions=obj.total_fee_minus_distributions,
            total_fee_withdrawn=obj.total_fee_withdrawn,
            total_liquidation_fee=obj.total_liquidation_fee,
            cumulative_funding_rate_long=obj.cumulative_funding_rate_long,
            cumulative_funding_rate_short=obj.cumulative_funding_rate_short,
            cumulative_social_loss=obj.cumulative_social_loss,
            ask_base_asset_reserve=obj.ask_base_asset_reserve,
            ask_quote_asset_reserve=obj.ask_quote_asset_reserve,
            bid_base_asset_reserve=obj.bid_base_asset_reserve,
            bid_quote_asset_reserve=obj.bid_quote_asset_reserve,
            last_oracle_normalised_price=obj.last_oracle_normalised_price,
            last_oracle_reserve_price_spread_pct=obj.last_oracle_reserve_price_spread_pct,
            last_bid_price_twap=obj.last_bid_price_twap,
            last_ask_price_twap=obj.last_ask_price_twap,
            last_mark_price_twap=obj.last_mark_price_twap,
            last_mark_price_twap5min=obj.last_mark_price_twap5min,
            last_update_slot=obj.last_update_slot,
            last_oracle_conf_pct=obj.last_oracle_conf_pct,
            net_revenue_since_last_funding=obj.net_revenue_since_last_funding,
            last_funding_rate_ts=obj.last_funding_rate_ts,
            funding_period=obj.funding_period,
            order_step_size=obj.order_step_size,
            order_tick_size=obj.order_tick_size,
            min_order_size=obj.min_order_size,
            max_position_size=obj.max_position_size,
            volume24h=obj.volume24h,
            long_intensity_volume=obj.long_intensity_volume,
            short_intensity_volume=obj.short_intensity_volume,
            last_trade_ts=obj.last_trade_ts,
            mark_std=obj.mark_std,
            last_mark_price_twap_ts=obj.last_mark_price_twap_ts,
            base_spread=obj.base_spread,
            max_spread=obj.max_spread,
            long_spread=obj.long_spread,
            short_spread=obj.short_spread,
            long_intensity_count=obj.long_intensity_count,
            short_intensity_count=obj.short_intensity_count,
            max_fill_reserve_fraction=obj.max_fill_reserve_fraction,
            max_slippage_ratio=obj.max_slippage_ratio,
            curve_update_intensity=obj.curve_update_intensity,
            amm_jit_intensity=obj.amm_jit_intensity,
            oracle_source=oracle_source.from_decoded(obj.oracle_source),
            last_oracle_valid=obj.last_oracle_valid,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "oracle": self.oracle,
            "historical_oracle_data": self.historical_oracle_data.to_encodable(),
            "base_asset_amount_per_lp": self.base_asset_amount_per_lp,
            "quote_asset_amount_per_lp": self.quote_asset_amount_per_lp,
            "fee_pool": self.fee_pool.to_encodable(),
            "base_asset_reserve": self.base_asset_reserve,
            "quote_asset_reserve": self.quote_asset_reserve,
            "concentration_coef": self.concentration_coef,
            "min_base_asset_reserve": self.min_base_asset_reserve,
            "max_base_asset_reserve": self.max_base_asset_reserve,
            "sqrt_k": self.sqrt_k,
            "peg_multiplier": self.peg_multiplier,
            "terminal_quote_asset_reserve": self.terminal_quote_asset_reserve,
            "base_asset_amount_long": self.base_asset_amount_long,
            "base_asset_amount_short": self.base_asset_amount_short,
            "base_asset_amount_with_amm": self.base_asset_amount_with_amm,
            "base_asset_amount_with_unsettled_lp": self.base_asset_amount_with_unsettled_lp,
            "max_open_interest": self.max_open_interest,
            "quote_asset_amount_long": self.quote_asset_amount_long,
            "quote_asset_amount_short": self.quote_asset_amount_short,
            "quote_entry_amount_long": self.quote_entry_amount_long,
            "quote_entry_amount_short": self.quote_entry_amount_short,
            "user_lp_shares": self.user_lp_shares,
            "last_funding_rate": self.last_funding_rate,
            "last_funding_rate_long": self.last_funding_rate_long,
            "last_funding_rate_short": self.last_funding_rate_short,
            "last24h_avg_funding_rate": self.last24h_avg_funding_rate,
            "total_fee": self.total_fee,
            "total_mm_fee": self.total_mm_fee,
            "total_exchange_fee": self.total_exchange_fee,
            "total_fee_minus_distributions": self.total_fee_minus_distributions,
            "total_fee_withdrawn": self.total_fee_withdrawn,
            "total_liquidation_fee": self.total_liquidation_fee,
            "cumulative_funding_rate_long": self.cumulative_funding_rate_long,
            "cumulative_funding_rate_short": self.cumulative_funding_rate_short,
            "cumulative_social_loss": self.cumulative_social_loss,
            "ask_base_asset_reserve": self.ask_base_asset_reserve,
            "ask_quote_asset_reserve": self.ask_quote_asset_reserve,
            "bid_base_asset_reserve": self.bid_base_asset_reserve,
            "bid_quote_asset_reserve": self.bid_quote_asset_reserve,
            "last_oracle_normalised_price": self.last_oracle_normalised_price,
            "last_oracle_reserve_price_spread_pct": self.last_oracle_reserve_price_spread_pct,
            "last_bid_price_twap": self.last_bid_price_twap,
            "last_ask_price_twap": self.last_ask_price_twap,
            "last_mark_price_twap": self.last_mark_price_twap,
            "last_mark_price_twap5min": self.last_mark_price_twap5min,
            "last_update_slot": self.last_update_slot,
            "last_oracle_conf_pct": self.last_oracle_conf_pct,
            "net_revenue_since_last_funding": self.net_revenue_since_last_funding,
            "last_funding_rate_ts": self.last_funding_rate_ts,
            "funding_period": self.funding_period,
            "order_step_size": self.order_step_size,
            "order_tick_size": self.order_tick_size,
            "min_order_size": self.min_order_size,
            "max_position_size": self.max_position_size,
            "volume24h": self.volume24h,
            "long_intensity_volume": self.long_intensity_volume,
            "short_intensity_volume": self.short_intensity_volume,
            "last_trade_ts": self.last_trade_ts,
            "mark_std": self.mark_std,
            "last_mark_price_twap_ts": self.last_mark_price_twap_ts,
            "base_spread": self.base_spread,
            "max_spread": self.max_spread,
            "long_spread": self.long_spread,
            "short_spread": self.short_spread,
            "long_intensity_count": self.long_intensity_count,
            "short_intensity_count": self.short_intensity_count,
            "max_fill_reserve_fraction": self.max_fill_reserve_fraction,
            "max_slippage_ratio": self.max_slippage_ratio,
            "curve_update_intensity": self.curve_update_intensity,
            "amm_jit_intensity": self.amm_jit_intensity,
            "oracle_source": self.oracle_source.to_encodable(),
            "last_oracle_valid": self.last_oracle_valid,
        }

    def to_json(self) -> AMMJSON:
        return {
            "oracle": str(self.oracle),
            "historical_oracle_data": self.historical_oracle_data.to_json(),
            "base_asset_amount_per_lp": self.base_asset_amount_per_lp,
            "quote_asset_amount_per_lp": self.quote_asset_amount_per_lp,
            "fee_pool": self.fee_pool.to_json(),
            "base_asset_reserve": self.base_asset_reserve,
            "quote_asset_reserve": self.quote_asset_reserve,
            "concentration_coef": self.concentration_coef,
            "min_base_asset_reserve": self.min_base_asset_reserve,
            "max_base_asset_reserve": self.max_base_asset_reserve,
            "sqrt_k": self.sqrt_k,
            "peg_multiplier": self.peg_multiplier,
            "terminal_quote_asset_reserve": self.terminal_quote_asset_reserve,
            "base_asset_amount_long": self.base_asset_amount_long,
            "base_asset_amount_short": self.base_asset_amount_short,
            "base_asset_amount_with_amm": self.base_asset_amount_with_amm,
            "base_asset_amount_with_unsettled_lp": self.base_asset_amount_with_unsettled_lp,
            "max_open_interest": self.max_open_interest,
            "quote_asset_amount_long": self.quote_asset_amount_long,
            "quote_asset_amount_short": self.quote_asset_amount_short,
            "quote_entry_amount_long": self.quote_entry_amount_long,
            "quote_entry_amount_short": self.quote_entry_amount_short,
            "user_lp_shares": self.user_lp_shares,
            "last_funding_rate": self.last_funding_rate,
            "last_funding_rate_long": self.last_funding_rate_long,
            "last_funding_rate_short": self.last_funding_rate_short,
            "last24h_avg_funding_rate": self.last24h_avg_funding_rate,
            "total_fee": self.total_fee,
            "total_mm_fee": self.total_mm_fee,
            "total_exchange_fee": self.total_exchange_fee,
            "total_fee_minus_distributions": self.total_fee_minus_distributions,
            "total_fee_withdrawn": self.total_fee_withdrawn,
            "total_liquidation_fee": self.total_liquidation_fee,
            "cumulative_funding_rate_long": self.cumulative_funding_rate_long,
            "cumulative_funding_rate_short": self.cumulative_funding_rate_short,
            "cumulative_social_loss": self.cumulative_social_loss,
            "ask_base_asset_reserve": self.ask_base_asset_reserve,
            "ask_quote_asset_reserve": self.ask_quote_asset_reserve,
            "bid_base_asset_reserve": self.bid_base_asset_reserve,
            "bid_quote_asset_reserve": self.bid_quote_asset_reserve,
            "last_oracle_normalised_price": self.last_oracle_normalised_price,
            "last_oracle_reserve_price_spread_pct": self.last_oracle_reserve_price_spread_pct,
            "last_bid_price_twap": self.last_bid_price_twap,
            "last_ask_price_twap": self.last_ask_price_twap,
            "last_mark_price_twap": self.last_mark_price_twap,
            "last_mark_price_twap5min": self.last_mark_price_twap5min,
            "last_update_slot": self.last_update_slot,
            "last_oracle_conf_pct": self.last_oracle_conf_pct,
            "net_revenue_since_last_funding": self.net_revenue_since_last_funding,
            "last_funding_rate_ts": self.last_funding_rate_ts,
            "funding_period": self.funding_period,
            "order_step_size": self.order_step_size,
            "order_tick_size": self.order_tick_size,
            "min_order_size": self.min_order_size,
            "max_position_size": self.max_position_size,
            "volume24h": self.volume24h,
            "long_intensity_volume": self.long_intensity_volume,
            "short_intensity_volume": self.short_intensity_volume,
            "last_trade_ts": self.last_trade_ts,
            "mark_std": self.mark_std,
            "last_mark_price_twap_ts": self.last_mark_price_twap_ts,
            "base_spread": self.base_spread,
            "max_spread": self.max_spread,
            "long_spread": self.long_spread,
            "short_spread": self.short_spread,
            "long_intensity_count": self.long_intensity_count,
            "short_intensity_count": self.short_intensity_count,
            "max_fill_reserve_fraction": self.max_fill_reserve_fraction,
            "max_slippage_ratio": self.max_slippage_ratio,
            "curve_update_intensity": self.curve_update_intensity,
            "amm_jit_intensity": self.amm_jit_intensity,
            "oracle_source": self.oracle_source.to_json(),
            "last_oracle_valid": self.last_oracle_valid,
        }

    @classmethod
    def from_json(cls, obj: AMMJSON) -> "AMM":
        return cls(
            oracle=PublicKey(obj["oracle"]),
            historical_oracle_data=historical_oracle_data.HistoricalOracleData.from_json(
                obj["historical_oracle_data"]
            ),
            base_asset_amount_per_lp=obj["base_asset_amount_per_lp"],
            quote_asset_amount_per_lp=obj["quote_asset_amount_per_lp"],
            fee_pool=pool_balance.PoolBalance.from_json(obj["fee_pool"]),
            base_asset_reserve=obj["base_asset_reserve"],
            quote_asset_reserve=obj["quote_asset_reserve"],
            concentration_coef=obj["concentration_coef"],
            min_base_asset_reserve=obj["min_base_asset_reserve"],
            max_base_asset_reserve=obj["max_base_asset_reserve"],
            sqrt_k=obj["sqrt_k"],
            peg_multiplier=obj["peg_multiplier"],
            terminal_quote_asset_reserve=obj["terminal_quote_asset_reserve"],
            base_asset_amount_long=obj["base_asset_amount_long"],
            base_asset_amount_short=obj["base_asset_amount_short"],
            base_asset_amount_with_amm=obj["base_asset_amount_with_amm"],
            base_asset_amount_with_unsettled_lp=obj[
                "base_asset_amount_with_unsettled_lp"
            ],
            max_open_interest=obj["max_open_interest"],
            quote_asset_amount_long=obj["quote_asset_amount_long"],
            quote_asset_amount_short=obj["quote_asset_amount_short"],
            quote_entry_amount_long=obj["quote_entry_amount_long"],
            quote_entry_amount_short=obj["quote_entry_amount_short"],
            user_lp_shares=obj["user_lp_shares"],
            last_funding_rate=obj["last_funding_rate"],
            last_funding_rate_long=obj["last_funding_rate_long"],
            last_funding_rate_short=obj["last_funding_rate_short"],
            last24h_avg_funding_rate=obj["last24h_avg_funding_rate"],
            total_fee=obj["total_fee"],
            total_mm_fee=obj["total_mm_fee"],
            total_exchange_fee=obj["total_exchange_fee"],
            total_fee_minus_distributions=obj["total_fee_minus_distributions"],
            total_fee_withdrawn=obj["total_fee_withdrawn"],
            total_liquidation_fee=obj["total_liquidation_fee"],
            cumulative_funding_rate_long=obj["cumulative_funding_rate_long"],
            cumulative_funding_rate_short=obj["cumulative_funding_rate_short"],
            cumulative_social_loss=obj["cumulative_social_loss"],
            ask_base_asset_reserve=obj["ask_base_asset_reserve"],
            ask_quote_asset_reserve=obj["ask_quote_asset_reserve"],
            bid_base_asset_reserve=obj["bid_base_asset_reserve"],
            bid_quote_asset_reserve=obj["bid_quote_asset_reserve"],
            last_oracle_normalised_price=obj["last_oracle_normalised_price"],
            last_oracle_reserve_price_spread_pct=obj[
                "last_oracle_reserve_price_spread_pct"
            ],
            last_bid_price_twap=obj["last_bid_price_twap"],
            last_ask_price_twap=obj["last_ask_price_twap"],
            last_mark_price_twap=obj["last_mark_price_twap"],
            last_mark_price_twap5min=obj["last_mark_price_twap5min"],
            last_update_slot=obj["last_update_slot"],
            last_oracle_conf_pct=obj["last_oracle_conf_pct"],
            net_revenue_since_last_funding=obj["net_revenue_since_last_funding"],
            last_funding_rate_ts=obj["last_funding_rate_ts"],
            funding_period=obj["funding_period"],
            order_step_size=obj["order_step_size"],
            order_tick_size=obj["order_tick_size"],
            min_order_size=obj["min_order_size"],
            max_position_size=obj["max_position_size"],
            volume24h=obj["volume24h"],
            long_intensity_volume=obj["long_intensity_volume"],
            short_intensity_volume=obj["short_intensity_volume"],
            last_trade_ts=obj["last_trade_ts"],
            mark_std=obj["mark_std"],
            last_mark_price_twap_ts=obj["last_mark_price_twap_ts"],
            base_spread=obj["base_spread"],
            max_spread=obj["max_spread"],
            long_spread=obj["long_spread"],
            short_spread=obj["short_spread"],
            long_intensity_count=obj["long_intensity_count"],
            short_intensity_count=obj["short_intensity_count"],
            max_fill_reserve_fraction=obj["max_fill_reserve_fraction"],
            max_slippage_ratio=obj["max_slippage_ratio"],
            curve_update_intensity=obj["curve_update_intensity"],
            amm_jit_intensity=obj["amm_jit_intensity"],
            oracle_source=oracle_source.from_json(obj["oracle_source"]),
            last_oracle_valid=obj["last_oracle_valid"],
        )
