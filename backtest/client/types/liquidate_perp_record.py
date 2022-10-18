from __future__ import annotations
import typing
from dataclasses import dataclass
from construct import Container
import borsh_construct as borsh


class LiquidatePerpRecordJSON(typing.TypedDict):
    market_index: int
    oracle_price: int
    base_asset_amount: int
    quote_asset_amount: int
    lp_shares: int
    fill_record_id: int
    user_order_id: int
    liquidator_order_id: int
    if_fee: int


@dataclass
class LiquidatePerpRecord:
    layout: typing.ClassVar = borsh.CStruct(
        "market_index" / borsh.U16,
        "oracle_price" / borsh.I128,
        "base_asset_amount" / borsh.I64,
        "quote_asset_amount" / borsh.I64,
        "lp_shares" / borsh.U64,
        "fill_record_id" / borsh.U64,
        "user_order_id" / borsh.U32,
        "liquidator_order_id" / borsh.U32,
        "if_fee" / borsh.U64,
    )
    market_index: int
    oracle_price: int
    base_asset_amount: int
    quote_asset_amount: int
    lp_shares: int
    fill_record_id: int
    user_order_id: int
    liquidator_order_id: int
    if_fee: int

    @classmethod
    def from_decoded(cls, obj: Container) -> "LiquidatePerpRecord":
        return cls(
            market_index=obj.market_index,
            oracle_price=obj.oracle_price,
            base_asset_amount=obj.base_asset_amount,
            quote_asset_amount=obj.quote_asset_amount,
            lp_shares=obj.lp_shares,
            fill_record_id=obj.fill_record_id,
            user_order_id=obj.user_order_id,
            liquidator_order_id=obj.liquidator_order_id,
            if_fee=obj.if_fee,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "market_index": self.market_index,
            "oracle_price": self.oracle_price,
            "base_asset_amount": self.base_asset_amount,
            "quote_asset_amount": self.quote_asset_amount,
            "lp_shares": self.lp_shares,
            "fill_record_id": self.fill_record_id,
            "user_order_id": self.user_order_id,
            "liquidator_order_id": self.liquidator_order_id,
            "if_fee": self.if_fee,
        }

    def to_json(self) -> LiquidatePerpRecordJSON:
        return {
            "market_index": self.market_index,
            "oracle_price": self.oracle_price,
            "base_asset_amount": self.base_asset_amount,
            "quote_asset_amount": self.quote_asset_amount,
            "lp_shares": self.lp_shares,
            "fill_record_id": self.fill_record_id,
            "user_order_id": self.user_order_id,
            "liquidator_order_id": self.liquidator_order_id,
            "if_fee": self.if_fee,
        }

    @classmethod
    def from_json(cls, obj: LiquidatePerpRecordJSON) -> "LiquidatePerpRecord":
        return cls(
            market_index=obj["market_index"],
            oracle_price=obj["oracle_price"],
            base_asset_amount=obj["base_asset_amount"],
            quote_asset_amount=obj["quote_asset_amount"],
            lp_shares=obj["lp_shares"],
            fill_record_id=obj["fill_record_id"],
            user_order_id=obj["user_order_id"],
            liquidator_order_id=obj["liquidator_order_id"],
            if_fee=obj["if_fee"],
        )
