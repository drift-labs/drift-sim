from __future__ import annotations
import typing
from dataclasses import dataclass
from anchorpy.borsh_extension import EnumForCodegen
import borsh_construct as borsh


class ActiveJSON(typing.TypedDict):
    kind: typing.Literal["Active"]


class FundingPausedJSON(typing.TypedDict):
    kind: typing.Literal["FundingPaused"]


class AmmPausedJSON(typing.TypedDict):
    kind: typing.Literal["AmmPaused"]


class FillPausedJSON(typing.TypedDict):
    kind: typing.Literal["FillPaused"]


class LiqPausedJSON(typing.TypedDict):
    kind: typing.Literal["LiqPaused"]


class WithdrawPausedJSON(typing.TypedDict):
    kind: typing.Literal["WithdrawPaused"]


class PausedJSON(typing.TypedDict):
    kind: typing.Literal["Paused"]


@dataclass
class Active:
    discriminator: typing.ClassVar = 0
    kind: typing.ClassVar = "Active"

    @classmethod
    def to_json(cls) -> ActiveJSON:
        return ActiveJSON(
            kind="Active",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Active": {},
        }


@dataclass
class FundingPaused:
    discriminator: typing.ClassVar = 1
    kind: typing.ClassVar = "FundingPaused"

    @classmethod
    def to_json(cls) -> FundingPausedJSON:
        return FundingPausedJSON(
            kind="FundingPaused",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "FundingPaused": {},
        }


@dataclass
class AmmPaused:
    discriminator: typing.ClassVar = 2
    kind: typing.ClassVar = "AmmPaused"

    @classmethod
    def to_json(cls) -> AmmPausedJSON:
        return AmmPausedJSON(
            kind="AmmPaused",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "AmmPaused": {},
        }


@dataclass
class FillPaused:
    discriminator: typing.ClassVar = 3
    kind: typing.ClassVar = "FillPaused"

    @classmethod
    def to_json(cls) -> FillPausedJSON:
        return FillPausedJSON(
            kind="FillPaused",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "FillPaused": {},
        }


@dataclass
class LiqPaused:
    discriminator: typing.ClassVar = 4
    kind: typing.ClassVar = "LiqPaused"

    @classmethod
    def to_json(cls) -> LiqPausedJSON:
        return LiqPausedJSON(
            kind="LiqPaused",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "LiqPaused": {},
        }


@dataclass
class WithdrawPaused:
    discriminator: typing.ClassVar = 5
    kind: typing.ClassVar = "WithdrawPaused"

    @classmethod
    def to_json(cls) -> WithdrawPausedJSON:
        return WithdrawPausedJSON(
            kind="WithdrawPaused",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "WithdrawPaused": {},
        }


@dataclass
class Paused:
    discriminator: typing.ClassVar = 6
    kind: typing.ClassVar = "Paused"

    @classmethod
    def to_json(cls) -> PausedJSON:
        return PausedJSON(
            kind="Paused",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Paused": {},
        }


ExchangeStatusKind = typing.Union[
    Active, FundingPaused, AmmPaused, FillPaused, LiqPaused, WithdrawPaused, Paused
]
ExchangeStatusJSON = typing.Union[
    ActiveJSON,
    FundingPausedJSON,
    AmmPausedJSON,
    FillPausedJSON,
    LiqPausedJSON,
    WithdrawPausedJSON,
    PausedJSON,
]


def from_decoded(obj: dict) -> ExchangeStatusKind:
    if not isinstance(obj, dict):
        raise ValueError("Invalid enum object")
    if "Active" in obj:
        return Active()
    if "FundingPaused" in obj:
        return FundingPaused()
    if "AmmPaused" in obj:
        return AmmPaused()
    if "FillPaused" in obj:
        return FillPaused()
    if "LiqPaused" in obj:
        return LiqPaused()
    if "WithdrawPaused" in obj:
        return WithdrawPaused()
    if "Paused" in obj:
        return Paused()
    raise ValueError("Invalid enum object")


def from_json(obj: ExchangeStatusJSON) -> ExchangeStatusKind:
    if obj["kind"] == "Active":
        return Active()
    if obj["kind"] == "FundingPaused":
        return FundingPaused()
    if obj["kind"] == "AmmPaused":
        return AmmPaused()
    if obj["kind"] == "FillPaused":
        return FillPaused()
    if obj["kind"] == "LiqPaused":
        return LiqPaused()
    if obj["kind"] == "WithdrawPaused":
        return WithdrawPaused()
    if obj["kind"] == "Paused":
        return Paused()
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen(
    "Active" / borsh.CStruct(),
    "FundingPaused" / borsh.CStruct(),
    "AmmPaused" / borsh.CStruct(),
    "FillPaused" / borsh.CStruct(),
    "LiqPaused" / borsh.CStruct(),
    "WithdrawPaused" / borsh.CStruct(),
    "Paused" / borsh.CStruct(),
)
