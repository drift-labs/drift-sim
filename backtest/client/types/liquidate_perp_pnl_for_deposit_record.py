from __future__ import annotations
import typing
from dataclasses import dataclass
from construct import Container
import borsh_construct as borsh


class LiquidatePerpPnlForDepositRecordJSON(typing.TypedDict):
    perp_market_index: int
    market_oracle_price: int
    pnl_transfer: int
    asset_market_index: int
    asset_price: int
    asset_transfer: int


@dataclass
class LiquidatePerpPnlForDepositRecord:
    layout: typing.ClassVar = borsh.CStruct(
        "perp_market_index" / borsh.U16,
        "market_oracle_price" / borsh.I128,
        "pnl_transfer" / borsh.U128,
        "asset_market_index" / borsh.U16,
        "asset_price" / borsh.I128,
        "asset_transfer" / borsh.U128,
    )
    perp_market_index: int
    market_oracle_price: int
    pnl_transfer: int
    asset_market_index: int
    asset_price: int
    asset_transfer: int

    @classmethod
    def from_decoded(cls, obj: Container) -> "LiquidatePerpPnlForDepositRecord":
        return cls(
            perp_market_index=obj.perp_market_index,
            market_oracle_price=obj.market_oracle_price,
            pnl_transfer=obj.pnl_transfer,
            asset_market_index=obj.asset_market_index,
            asset_price=obj.asset_price,
            asset_transfer=obj.asset_transfer,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "perp_market_index": self.perp_market_index,
            "market_oracle_price": self.market_oracle_price,
            "pnl_transfer": self.pnl_transfer,
            "asset_market_index": self.asset_market_index,
            "asset_price": self.asset_price,
            "asset_transfer": self.asset_transfer,
        }

    def to_json(self) -> LiquidatePerpPnlForDepositRecordJSON:
        return {
            "perp_market_index": self.perp_market_index,
            "market_oracle_price": self.market_oracle_price,
            "pnl_transfer": self.pnl_transfer,
            "asset_market_index": self.asset_market_index,
            "asset_price": self.asset_price,
            "asset_transfer": self.asset_transfer,
        }

    @classmethod
    def from_json(
        cls, obj: LiquidatePerpPnlForDepositRecordJSON
    ) -> "LiquidatePerpPnlForDepositRecord":
        return cls(
            perp_market_index=obj["perp_market_index"],
            market_oracle_price=obj["market_oracle_price"],
            pnl_transfer=obj["pnl_transfer"],
            asset_market_index=obj["asset_market_index"],
            asset_price=obj["asset_price"],
            asset_transfer=obj["asset_transfer"],
        )
