from __future__ import annotations
import typing
from dataclasses import dataclass
from construct import Container
import borsh_construct as borsh


class PerpBankruptcyRecordJSON(typing.TypedDict):
    market_index: int
    pnl: int
    if_payment: int
    cumulative_funding_rate_delta: int


@dataclass
class PerpBankruptcyRecord:
    layout: typing.ClassVar = borsh.CStruct(
        "market_index" / borsh.U16,
        "pnl" / borsh.I128,
        "if_payment" / borsh.U128,
        "cumulative_funding_rate_delta" / borsh.I128,
    )
    market_index: int
    pnl: int
    if_payment: int
    cumulative_funding_rate_delta: int

    @classmethod
    def from_decoded(cls, obj: Container) -> "PerpBankruptcyRecord":
        return cls(
            market_index=obj.market_index,
            pnl=obj.pnl,
            if_payment=obj.if_payment,
            cumulative_funding_rate_delta=obj.cumulative_funding_rate_delta,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "market_index": self.market_index,
            "pnl": self.pnl,
            "if_payment": self.if_payment,
            "cumulative_funding_rate_delta": self.cumulative_funding_rate_delta,
        }

    def to_json(self) -> PerpBankruptcyRecordJSON:
        return {
            "market_index": self.market_index,
            "pnl": self.pnl,
            "if_payment": self.if_payment,
            "cumulative_funding_rate_delta": self.cumulative_funding_rate_delta,
        }

    @classmethod
    def from_json(cls, obj: PerpBankruptcyRecordJSON) -> "PerpBankruptcyRecord":
        return cls(
            market_index=obj["market_index"],
            pnl=obj["pnl"],
            if_payment=obj["if_payment"],
            cumulative_funding_rate_delta=obj["cumulative_funding_rate_delta"],
        )
