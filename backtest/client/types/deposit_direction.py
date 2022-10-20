from __future__ import annotations
import typing
from dataclasses import dataclass
from anchorpy.borsh_extension import EnumForCodegen
import borsh_construct as borsh


class DEPOSITJSON(typing.TypedDict):
    kind: typing.Literal["DEPOSIT"]


class WITHDRAWJSON(typing.TypedDict):
    kind: typing.Literal["WITHDRAW"]


@dataclass
class DEPOSIT:
    discriminator: typing.ClassVar = 0
    kind: typing.ClassVar = "DEPOSIT"

    @classmethod
    def to_json(cls) -> DEPOSITJSON:
        return DEPOSITJSON(
            kind="DEPOSIT",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "DEPOSIT": {},
        }


@dataclass
class WITHDRAW:
    discriminator: typing.ClassVar = 1
    kind: typing.ClassVar = "WITHDRAW"

    @classmethod
    def to_json(cls) -> WITHDRAWJSON:
        return WITHDRAWJSON(
            kind="WITHDRAW",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "WITHDRAW": {},
        }


DepositDirectionKind = typing.Union[DEPOSIT, WITHDRAW]
DepositDirectionJSON = typing.Union[DEPOSITJSON, WITHDRAWJSON]


def from_decoded(obj: dict) -> DepositDirectionKind:
    if not isinstance(obj, dict):
        raise ValueError("Invalid enum object")
    if "DEPOSIT" in obj:
        return DEPOSIT()
    if "WITHDRAW" in obj:
        return WITHDRAW()
    raise ValueError("Invalid enum object")


def from_json(obj: DepositDirectionJSON) -> DepositDirectionKind:
    if obj["kind"] == "DEPOSIT":
        return DEPOSIT()
    if obj["kind"] == "WITHDRAW":
        return WITHDRAW()
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen("DEPOSIT" / borsh.CStruct(), "WITHDRAW" / borsh.CStruct())
