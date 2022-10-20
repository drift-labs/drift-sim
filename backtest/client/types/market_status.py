from __future__ import annotations
import typing
from dataclasses import dataclass
from anchorpy.borsh_extension import EnumForCodegen
import borsh_construct as borsh


class InitializedJSON(typing.TypedDict):
    kind: typing.Literal["Initialized"]


class ActiveJSON(typing.TypedDict):
    kind: typing.Literal["Active"]


class FundingPausedJSON(typing.TypedDict):
    kind: typing.Literal["FundingPaused"]


class AmmPausedJSON(typing.TypedDict):
    kind: typing.Literal["AmmPaused"]


class FillPausedJSON(typing.TypedDict):
    kind: typing.Literal["FillPaused"]


class WithdrawPausedJSON(typing.TypedDict):
    kind: typing.Literal["WithdrawPaused"]


class ReduceOnlyJSON(typing.TypedDict):
    kind: typing.Literal["ReduceOnly"]


class SettlementJSON(typing.TypedDict):
    kind: typing.Literal["Settlement"]


class DelistedJSON(typing.TypedDict):
    kind: typing.Literal["Delisted"]


@dataclass
class Initialized:
    discriminator: typing.ClassVar = 0
    kind: typing.ClassVar = "Initialized"

    @classmethod
    def to_json(cls) -> InitializedJSON:
        return InitializedJSON(
            kind="Initialized",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Initialized": {},
        }


@dataclass
class Active:
    discriminator: typing.ClassVar = 1
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
    discriminator: typing.ClassVar = 2
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
    discriminator: typing.ClassVar = 3
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
    discriminator: typing.ClassVar = 4
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
class ReduceOnly:
    discriminator: typing.ClassVar = 6
    kind: typing.ClassVar = "ReduceOnly"

    @classmethod
    def to_json(cls) -> ReduceOnlyJSON:
        return ReduceOnlyJSON(
            kind="ReduceOnly",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "ReduceOnly": {},
        }


@dataclass
class Settlement:
    discriminator: typing.ClassVar = 7
    kind: typing.ClassVar = "Settlement"

    @classmethod
    def to_json(cls) -> SettlementJSON:
        return SettlementJSON(
            kind="Settlement",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Settlement": {},
        }


@dataclass
class Delisted:
    discriminator: typing.ClassVar = 8
    kind: typing.ClassVar = "Delisted"

    @classmethod
    def to_json(cls) -> DelistedJSON:
        return DelistedJSON(
            kind="Delisted",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Delisted": {},
        }


MarketStatusKind = typing.Union[
    Initialized,
    Active,
    FundingPaused,
    AmmPaused,
    FillPaused,
    WithdrawPaused,
    ReduceOnly,
    Settlement,
    Delisted,
]
MarketStatusJSON = typing.Union[
    InitializedJSON,
    ActiveJSON,
    FundingPausedJSON,
    AmmPausedJSON,
    FillPausedJSON,
    WithdrawPausedJSON,
    ReduceOnlyJSON,
    SettlementJSON,
    DelistedJSON,
]


def from_decoded(obj: dict) -> MarketStatusKind:
    if not isinstance(obj, dict):
        raise ValueError("Invalid enum object")
    if "Initialized" in obj:
        return Initialized()
    if "Active" in obj:
        return Active()
    if "FundingPaused" in obj:
        return FundingPaused()
    if "AmmPaused" in obj:
        return AmmPaused()
    if "FillPaused" in obj:
        return FillPaused()
    if "WithdrawPaused" in obj:
        return WithdrawPaused()
    if "ReduceOnly" in obj:
        return ReduceOnly()
    if "Settlement" in obj:
        return Settlement()
    if "Delisted" in obj:
        return Delisted()
    raise ValueError("Invalid enum object")


def from_json(obj: MarketStatusJSON) -> MarketStatusKind:
    if obj["kind"] == "Initialized":
        return Initialized()
    if obj["kind"] == "Active":
        return Active()
    if obj["kind"] == "FundingPaused":
        return FundingPaused()
    if obj["kind"] == "AmmPaused":
        return AmmPaused()
    if obj["kind"] == "FillPaused":
        return FillPaused()
    if obj["kind"] == "WithdrawPaused":
        return WithdrawPaused()
    if obj["kind"] == "ReduceOnly":
        return ReduceOnly()
    if obj["kind"] == "Settlement":
        return Settlement()
    if obj["kind"] == "Delisted":
        return Delisted()
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen(
    "Initialized" / borsh.CStruct(),
    "Active" / borsh.CStruct(),
    "FundingPaused" / borsh.CStruct(),
    "AmmPaused" / borsh.CStruct(),
    "FillPaused" / borsh.CStruct(),
    "WithdrawPaused" / borsh.CStruct(),
    "ReduceOnly" / borsh.CStruct(),
    "Settlement" / borsh.CStruct(),
    "Delisted" / borsh.CStruct(),
)
