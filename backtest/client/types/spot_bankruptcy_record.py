from __future__ import annotations
import typing
from dataclasses import dataclass
from construct import Container
import borsh_construct as borsh


class SpotBankruptcyRecordJSON(typing.TypedDict):
    market_index: int
    borrow_amount: int
    if_payment: int
    cumulative_deposit_interest_delta: int


@dataclass
class SpotBankruptcyRecord:
    layout: typing.ClassVar = borsh.CStruct(
        "market_index" / borsh.U16,
        "borrow_amount" / borsh.U128,
        "if_payment" / borsh.U128,
        "cumulative_deposit_interest_delta" / borsh.U128,
    )
    market_index: int
    borrow_amount: int
    if_payment: int
    cumulative_deposit_interest_delta: int

    @classmethod
    def from_decoded(cls, obj: Container) -> "SpotBankruptcyRecord":
        return cls(
            market_index=obj.market_index,
            borrow_amount=obj.borrow_amount,
            if_payment=obj.if_payment,
            cumulative_deposit_interest_delta=obj.cumulative_deposit_interest_delta,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "market_index": self.market_index,
            "borrow_amount": self.borrow_amount,
            "if_payment": self.if_payment,
            "cumulative_deposit_interest_delta": self.cumulative_deposit_interest_delta,
        }

    def to_json(self) -> SpotBankruptcyRecordJSON:
        return {
            "market_index": self.market_index,
            "borrow_amount": self.borrow_amount,
            "if_payment": self.if_payment,
            "cumulative_deposit_interest_delta": self.cumulative_deposit_interest_delta,
        }

    @classmethod
    def from_json(cls, obj: SpotBankruptcyRecordJSON) -> "SpotBankruptcyRecord":
        return cls(
            market_index=obj["market_index"],
            borrow_amount=obj["borrow_amount"],
            if_payment=obj["if_payment"],
            cumulative_deposit_interest_delta=obj["cumulative_deposit_interest_delta"],
        )
