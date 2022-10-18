from __future__ import annotations
import typing
from dataclasses import dataclass
from construct import Container
import borsh_construct as borsh


class PerpPositionJSON(typing.TypedDict):
    last_cumulative_funding_rate: int
    base_asset_amount: int
    quote_asset_amount: int
    quote_entry_amount: int
    open_bids: int
    open_asks: int
    settled_pnl: int
    lp_shares: int
    last_net_base_asset_amount_per_lp: int
    last_net_quote_asset_amount_per_lp: int
    remainder_base_asset_amount: int
    market_index: int
    open_orders: int
    padding: list[int]


@dataclass
class PerpPosition:
    layout: typing.ClassVar = borsh.CStruct(
        "last_cumulative_funding_rate" / borsh.I64,
        "base_asset_amount" / borsh.I64,
        "quote_asset_amount" / borsh.I64,
        "quote_entry_amount" / borsh.I64,
        "open_bids" / borsh.I64,
        "open_asks" / borsh.I64,
        "settled_pnl" / borsh.I64,
        "lp_shares" / borsh.U64,
        "last_net_base_asset_amount_per_lp" / borsh.I64,
        "last_net_quote_asset_amount_per_lp" / borsh.I64,
        "remainder_base_asset_amount" / borsh.I32,
        "market_index" / borsh.U16,
        "open_orders" / borsh.U8,
        "padding" / borsh.U8[1],
    )
    last_cumulative_funding_rate: int
    base_asset_amount: int
    quote_asset_amount: int
    quote_entry_amount: int
    open_bids: int
    open_asks: int
    settled_pnl: int
    lp_shares: int
    last_net_base_asset_amount_per_lp: int
    last_net_quote_asset_amount_per_lp: int
    remainder_base_asset_amount: int
    market_index: int
    open_orders: int
    padding: list[int]

    @classmethod
    def from_decoded(cls, obj: Container) -> "PerpPosition":
        return cls(
            last_cumulative_funding_rate=obj.last_cumulative_funding_rate,
            base_asset_amount=obj.base_asset_amount,
            quote_asset_amount=obj.quote_asset_amount,
            quote_entry_amount=obj.quote_entry_amount,
            open_bids=obj.open_bids,
            open_asks=obj.open_asks,
            settled_pnl=obj.settled_pnl,
            lp_shares=obj.lp_shares,
            last_net_base_asset_amount_per_lp=obj.last_net_base_asset_amount_per_lp,
            last_net_quote_asset_amount_per_lp=obj.last_net_quote_asset_amount_per_lp,
            remainder_base_asset_amount=obj.remainder_base_asset_amount,
            market_index=obj.market_index,
            open_orders=obj.open_orders,
            padding=obj.padding,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "last_cumulative_funding_rate": self.last_cumulative_funding_rate,
            "base_asset_amount": self.base_asset_amount,
            "quote_asset_amount": self.quote_asset_amount,
            "quote_entry_amount": self.quote_entry_amount,
            "open_bids": self.open_bids,
            "open_asks": self.open_asks,
            "settled_pnl": self.settled_pnl,
            "lp_shares": self.lp_shares,
            "last_net_base_asset_amount_per_lp": self.last_net_base_asset_amount_per_lp,
            "last_net_quote_asset_amount_per_lp": self.last_net_quote_asset_amount_per_lp,
            "remainder_base_asset_amount": self.remainder_base_asset_amount,
            "market_index": self.market_index,
            "open_orders": self.open_orders,
            "padding": self.padding,
        }

    def to_json(self) -> PerpPositionJSON:
        return {
            "last_cumulative_funding_rate": self.last_cumulative_funding_rate,
            "base_asset_amount": self.base_asset_amount,
            "quote_asset_amount": self.quote_asset_amount,
            "quote_entry_amount": self.quote_entry_amount,
            "open_bids": self.open_bids,
            "open_asks": self.open_asks,
            "settled_pnl": self.settled_pnl,
            "lp_shares": self.lp_shares,
            "last_net_base_asset_amount_per_lp": self.last_net_base_asset_amount_per_lp,
            "last_net_quote_asset_amount_per_lp": self.last_net_quote_asset_amount_per_lp,
            "remainder_base_asset_amount": self.remainder_base_asset_amount,
            "market_index": self.market_index,
            "open_orders": self.open_orders,
            "padding": self.padding,
        }

    @classmethod
    def from_json(cls, obj: PerpPositionJSON) -> "PerpPosition":
        return cls(
            last_cumulative_funding_rate=obj["last_cumulative_funding_rate"],
            base_asset_amount=obj["base_asset_amount"],
            quote_asset_amount=obj["quote_asset_amount"],
            quote_entry_amount=obj["quote_entry_amount"],
            open_bids=obj["open_bids"],
            open_asks=obj["open_asks"],
            settled_pnl=obj["settled_pnl"],
            lp_shares=obj["lp_shares"],
            last_net_base_asset_amount_per_lp=obj["last_net_base_asset_amount_per_lp"],
            last_net_quote_asset_amount_per_lp=obj[
                "last_net_quote_asset_amount_per_lp"
            ],
            remainder_base_asset_amount=obj["remainder_base_asset_amount"],
            market_index=obj["market_index"],
            open_orders=obj["open_orders"],
            padding=obj["padding"],
        )
