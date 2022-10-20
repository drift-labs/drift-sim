from __future__ import annotations
import typing
from dataclasses import dataclass
from construct import Container
import borsh_construct as borsh


class PoolBalanceJSON(typing.TypedDict):
    scaled_balance: int
    market_index: int
    padding: list[int]


@dataclass
class PoolBalance:
    layout: typing.ClassVar = borsh.CStruct(
        "scaled_balance" / borsh.U128,
        "market_index" / borsh.U16,
        "padding" / borsh.U8[6],
    )
    scaled_balance: int
    market_index: int
    padding: list[int]

    @classmethod
    def from_decoded(cls, obj: Container) -> "PoolBalance":
        return cls(
            scaled_balance=obj.scaled_balance,
            market_index=obj.market_index,
            padding=obj.padding,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "scaled_balance": self.scaled_balance,
            "market_index": self.market_index,
            "padding": self.padding,
        }

    def to_json(self) -> PoolBalanceJSON:
        return {
            "scaled_balance": self.scaled_balance,
            "market_index": self.market_index,
            "padding": self.padding,
        }

    @classmethod
    def from_json(cls, obj: PoolBalanceJSON) -> "PoolBalance":
        return cls(
            scaled_balance=obj["scaled_balance"],
            market_index=obj["market_index"],
            padding=obj["padding"],
        )
