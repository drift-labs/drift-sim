from __future__ import annotations
import typing
from dataclasses import dataclass
from anchorpy.borsh_extension import EnumForCodegen
import borsh_construct as borsh


class LiquidatePerpJSON(typing.TypedDict):
    kind: typing.Literal["LiquidatePerp"]


class LiquidateSpotJSON(typing.TypedDict):
    kind: typing.Literal["LiquidateSpot"]


class LiquidateBorrowForPerpPnlJSON(typing.TypedDict):
    kind: typing.Literal["LiquidateBorrowForPerpPnl"]


class LiquidatePerpPnlForDepositJSON(typing.TypedDict):
    kind: typing.Literal["LiquidatePerpPnlForDeposit"]


class PerpBankruptcyJSON(typing.TypedDict):
    kind: typing.Literal["PerpBankruptcy"]


class SpotBankruptcyJSON(typing.TypedDict):
    kind: typing.Literal["SpotBankruptcy"]


@dataclass
class LiquidatePerp:
    discriminator: typing.ClassVar = 0
    kind: typing.ClassVar = "LiquidatePerp"

    @classmethod
    def to_json(cls) -> LiquidatePerpJSON:
        return LiquidatePerpJSON(
            kind="LiquidatePerp",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "LiquidatePerp": {},
        }


@dataclass
class LiquidateSpot:
    discriminator: typing.ClassVar = 1
    kind: typing.ClassVar = "LiquidateSpot"

    @classmethod
    def to_json(cls) -> LiquidateSpotJSON:
        return LiquidateSpotJSON(
            kind="LiquidateSpot",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "LiquidateSpot": {},
        }


@dataclass
class LiquidateBorrowForPerpPnl:
    discriminator: typing.ClassVar = 2
    kind: typing.ClassVar = "LiquidateBorrowForPerpPnl"

    @classmethod
    def to_json(cls) -> LiquidateBorrowForPerpPnlJSON:
        return LiquidateBorrowForPerpPnlJSON(
            kind="LiquidateBorrowForPerpPnl",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "LiquidateBorrowForPerpPnl": {},
        }


@dataclass
class LiquidatePerpPnlForDeposit:
    discriminator: typing.ClassVar = 3
    kind: typing.ClassVar = "LiquidatePerpPnlForDeposit"

    @classmethod
    def to_json(cls) -> LiquidatePerpPnlForDepositJSON:
        return LiquidatePerpPnlForDepositJSON(
            kind="LiquidatePerpPnlForDeposit",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "LiquidatePerpPnlForDeposit": {},
        }


@dataclass
class PerpBankruptcy:
    discriminator: typing.ClassVar = 4
    kind: typing.ClassVar = "PerpBankruptcy"

    @classmethod
    def to_json(cls) -> PerpBankruptcyJSON:
        return PerpBankruptcyJSON(
            kind="PerpBankruptcy",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "PerpBankruptcy": {},
        }


@dataclass
class SpotBankruptcy:
    discriminator: typing.ClassVar = 5
    kind: typing.ClassVar = "SpotBankruptcy"

    @classmethod
    def to_json(cls) -> SpotBankruptcyJSON:
        return SpotBankruptcyJSON(
            kind="SpotBankruptcy",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "SpotBankruptcy": {},
        }


LiquidationTypeKind = typing.Union[
    LiquidatePerp,
    LiquidateSpot,
    LiquidateBorrowForPerpPnl,
    LiquidatePerpPnlForDeposit,
    PerpBankruptcy,
    SpotBankruptcy,
]
LiquidationTypeJSON = typing.Union[
    LiquidatePerpJSON,
    LiquidateSpotJSON,
    LiquidateBorrowForPerpPnlJSON,
    LiquidatePerpPnlForDepositJSON,
    PerpBankruptcyJSON,
    SpotBankruptcyJSON,
]


def from_decoded(obj: dict) -> LiquidationTypeKind:
    if not isinstance(obj, dict):
        raise ValueError("Invalid enum object")
    if "LiquidatePerp" in obj:
        return LiquidatePerp()
    if "LiquidateSpot" in obj:
        return LiquidateSpot()
    if "LiquidateBorrowForPerpPnl" in obj:
        return LiquidateBorrowForPerpPnl()
    if "LiquidatePerpPnlForDeposit" in obj:
        return LiquidatePerpPnlForDeposit()
    if "PerpBankruptcy" in obj:
        return PerpBankruptcy()
    if "SpotBankruptcy" in obj:
        return SpotBankruptcy()
    raise ValueError("Invalid enum object")


def from_json(obj: LiquidationTypeJSON) -> LiquidationTypeKind:
    if obj["kind"] == "LiquidatePerp":
        return LiquidatePerp()
    if obj["kind"] == "LiquidateSpot":
        return LiquidateSpot()
    if obj["kind"] == "LiquidateBorrowForPerpPnl":
        return LiquidateBorrowForPerpPnl()
    if obj["kind"] == "LiquidatePerpPnlForDeposit":
        return LiquidatePerpPnlForDeposit()
    if obj["kind"] == "PerpBankruptcy":
        return PerpBankruptcy()
    if obj["kind"] == "SpotBankruptcy":
        return SpotBankruptcy()
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen(
    "LiquidatePerp" / borsh.CStruct(),
    "LiquidateSpot" / borsh.CStruct(),
    "LiquidateBorrowForPerpPnl" / borsh.CStruct(),
    "LiquidatePerpPnlForDeposit" / borsh.CStruct(),
    "PerpBankruptcy" / borsh.CStruct(),
    "SpotBankruptcy" / borsh.CStruct(),
)
