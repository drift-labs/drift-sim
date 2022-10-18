from __future__ import annotations
import typing
from dataclasses import dataclass
from construct import Container
import borsh_construct as borsh


class LiquidateBorrowForPerpPnlRecordJSON(typing.TypedDict):
    perp_market_index: int
    market_oracle_price: int
    pnl_transfer: int
    liability_market_index: int
    liability_price: int
    liability_transfer: int


@dataclass
class LiquidateBorrowForPerpPnlRecord:
    layout: typing.ClassVar = borsh.CStruct(
        "perp_market_index" / borsh.U16,
        "market_oracle_price" / borsh.I128,
        "pnl_transfer" / borsh.U128,
        "liability_market_index" / borsh.U16,
        "liability_price" / borsh.I128,
        "liability_transfer" / borsh.U128,
    )
    perp_market_index: int
    market_oracle_price: int
    pnl_transfer: int
    liability_market_index: int
    liability_price: int
    liability_transfer: int

    @classmethod
    def from_decoded(cls, obj: Container) -> "LiquidateBorrowForPerpPnlRecord":
        return cls(
            perp_market_index=obj.perp_market_index,
            market_oracle_price=obj.market_oracle_price,
            pnl_transfer=obj.pnl_transfer,
            liability_market_index=obj.liability_market_index,
            liability_price=obj.liability_price,
            liability_transfer=obj.liability_transfer,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "perp_market_index": self.perp_market_index,
            "market_oracle_price": self.market_oracle_price,
            "pnl_transfer": self.pnl_transfer,
            "liability_market_index": self.liability_market_index,
            "liability_price": self.liability_price,
            "liability_transfer": self.liability_transfer,
        }

    def to_json(self) -> LiquidateBorrowForPerpPnlRecordJSON:
        return {
            "perp_market_index": self.perp_market_index,
            "market_oracle_price": self.market_oracle_price,
            "pnl_transfer": self.pnl_transfer,
            "liability_market_index": self.liability_market_index,
            "liability_price": self.liability_price,
            "liability_transfer": self.liability_transfer,
        }

    @classmethod
    def from_json(
        cls, obj: LiquidateBorrowForPerpPnlRecordJSON
    ) -> "LiquidateBorrowForPerpPnlRecord":
        return cls(
            perp_market_index=obj["perp_market_index"],
            market_oracle_price=obj["market_oracle_price"],
            pnl_transfer=obj["pnl_transfer"],
            liability_market_index=obj["liability_market_index"],
            liability_price=obj["liability_price"],
            liability_transfer=obj["liability_transfer"],
        )
