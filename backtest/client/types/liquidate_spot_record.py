from __future__ import annotations
import typing
from dataclasses import dataclass
from construct import Container
import borsh_construct as borsh


class LiquidateSpotRecordJSON(typing.TypedDict):
    asset_market_index: int
    asset_price: int
    asset_transfer: int
    liability_market_index: int
    liability_price: int
    liability_transfer: int
    if_fee: int


@dataclass
class LiquidateSpotRecord:
    layout: typing.ClassVar = borsh.CStruct(
        "asset_market_index" / borsh.U16,
        "asset_price" / borsh.I128,
        "asset_transfer" / borsh.U128,
        "liability_market_index" / borsh.U16,
        "liability_price" / borsh.I128,
        "liability_transfer" / borsh.U128,
        "if_fee" / borsh.U64,
    )
    asset_market_index: int
    asset_price: int
    asset_transfer: int
    liability_market_index: int
    liability_price: int
    liability_transfer: int
    if_fee: int

    @classmethod
    def from_decoded(cls, obj: Container) -> "LiquidateSpotRecord":
        return cls(
            asset_market_index=obj.asset_market_index,
            asset_price=obj.asset_price,
            asset_transfer=obj.asset_transfer,
            liability_market_index=obj.liability_market_index,
            liability_price=obj.liability_price,
            liability_transfer=obj.liability_transfer,
            if_fee=obj.if_fee,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "asset_market_index": self.asset_market_index,
            "asset_price": self.asset_price,
            "asset_transfer": self.asset_transfer,
            "liability_market_index": self.liability_market_index,
            "liability_price": self.liability_price,
            "liability_transfer": self.liability_transfer,
            "if_fee": self.if_fee,
        }

    def to_json(self) -> LiquidateSpotRecordJSON:
        return {
            "asset_market_index": self.asset_market_index,
            "asset_price": self.asset_price,
            "asset_transfer": self.asset_transfer,
            "liability_market_index": self.liability_market_index,
            "liability_price": self.liability_price,
            "liability_transfer": self.liability_transfer,
            "if_fee": self.if_fee,
        }

    @classmethod
    def from_json(cls, obj: LiquidateSpotRecordJSON) -> "LiquidateSpotRecord":
        return cls(
            asset_market_index=obj["asset_market_index"],
            asset_price=obj["asset_price"],
            asset_transfer=obj["asset_transfer"],
            liability_market_index=obj["liability_market_index"],
            liability_price=obj["liability_price"],
            liability_transfer=obj["liability_transfer"],
            if_fee=obj["if_fee"],
        )
