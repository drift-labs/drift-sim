from __future__ import annotations
from . import (
    spot_balance_type,
)
import typing
from dataclasses import dataclass
from construct import Container
import borsh_construct as borsh


class SpotPositionJSON(typing.TypedDict):
    scaled_balance: int
    open_bids: int
    open_asks: int
    cumulative_deposits: int
    market_index: int
    balance_type: spot_balance_type.SpotBalanceTypeJSON
    open_orders: int
    padding: list[int]


@dataclass
class SpotPosition:
    layout: typing.ClassVar = borsh.CStruct(
        "scaled_balance" / borsh.U64,
        "open_bids" / borsh.I64,
        "open_asks" / borsh.I64,
        "cumulative_deposits" / borsh.I64,
        "market_index" / borsh.U16,
        "balance_type" / spot_balance_type.layout,
        "open_orders" / borsh.U8,
        "padding" / borsh.U8[4],
    )
    scaled_balance: int
    open_bids: int
    open_asks: int
    cumulative_deposits: int
    market_index: int
    balance_type: spot_balance_type.SpotBalanceTypeKind
    open_orders: int
    padding: list[int]

    @classmethod
    def from_decoded(cls, obj: Container) -> "SpotPosition":
        return cls(
            scaled_balance=obj.scaled_balance,
            open_bids=obj.open_bids,
            open_asks=obj.open_asks,
            cumulative_deposits=obj.cumulative_deposits,
            market_index=obj.market_index,
            balance_type=spot_balance_type.from_decoded(obj.balance_type),
            open_orders=obj.open_orders,
            padding=obj.padding,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "scaled_balance": self.scaled_balance,
            "open_bids": self.open_bids,
            "open_asks": self.open_asks,
            "cumulative_deposits": self.cumulative_deposits,
            "market_index": self.market_index,
            "balance_type": self.balance_type.to_encodable(),
            "open_orders": self.open_orders,
            "padding": self.padding,
        }

    def to_json(self) -> SpotPositionJSON:
        return {
            "scaled_balance": self.scaled_balance,
            "open_bids": self.open_bids,
            "open_asks": self.open_asks,
            "cumulative_deposits": self.cumulative_deposits,
            "market_index": self.market_index,
            "balance_type": self.balance_type.to_json(),
            "open_orders": self.open_orders,
            "padding": self.padding,
        }

    @classmethod
    def from_json(cls, obj: SpotPositionJSON) -> "SpotPosition":
        return cls(
            scaled_balance=obj["scaled_balance"],
            open_bids=obj["open_bids"],
            open_asks=obj["open_asks"],
            cumulative_deposits=obj["cumulative_deposits"],
            market_index=obj["market_index"],
            balance_type=spot_balance_type.from_json(obj["balance_type"]),
            open_orders=obj["open_orders"],
            padding=obj["padding"],
        )
