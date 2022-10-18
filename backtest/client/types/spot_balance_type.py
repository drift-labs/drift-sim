from __future__ import annotations
import typing
from dataclasses import dataclass
from anchorpy.borsh_extension import EnumForCodegen
import borsh_construct as borsh


class DepositJSON(typing.TypedDict):
    kind: typing.Literal["Deposit"]


class BorrowJSON(typing.TypedDict):
    kind: typing.Literal["Borrow"]


@dataclass
class Deposit:
    discriminator: typing.ClassVar = 0
    kind: typing.ClassVar = "Deposit"

    @classmethod
    def to_json(cls) -> DepositJSON:
        return DepositJSON(
            kind="Deposit",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Deposit": {},
        }


@dataclass
class Borrow:
    discriminator: typing.ClassVar = 1
    kind: typing.ClassVar = "Borrow"

    @classmethod
    def to_json(cls) -> BorrowJSON:
        return BorrowJSON(
            kind="Borrow",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Borrow": {},
        }


SpotBalanceTypeKind = typing.Union[Deposit, Borrow]
SpotBalanceTypeJSON = typing.Union[DepositJSON, BorrowJSON]


def from_decoded(obj: dict) -> SpotBalanceTypeKind:
    if not isinstance(obj, dict):
        raise ValueError("Invalid enum object")
    if "Deposit" in obj:
        return Deposit()
    if "Borrow" in obj:
        return Borrow()
    raise ValueError("Invalid enum object")


def from_json(obj: SpotBalanceTypeJSON) -> SpotBalanceTypeKind:
    if obj["kind"] == "Deposit":
        return Deposit()
    if obj["kind"] == "Borrow":
        return Borrow()
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen("Deposit" / borsh.CStruct(), "Borrow" / borsh.CStruct())
