from __future__ import annotations
import typing
from dataclasses import dataclass
from anchorpy.borsh_extension import EnumForCodegen
import borsh_construct as borsh


class UpdateFundingJSON(typing.TypedDict):
    kind: typing.Literal["UpdateFunding"]


class SettlePnlJSON(typing.TypedDict):
    kind: typing.Literal["SettlePnl"]


class TriggerOrderJSON(typing.TypedDict):
    kind: typing.Literal["TriggerOrder"]


class FillOrderMatchJSON(typing.TypedDict):
    kind: typing.Literal["FillOrderMatch"]


class FillOrderAmmJSON(typing.TypedDict):
    kind: typing.Literal["FillOrderAmm"]


class LiquidateJSON(typing.TypedDict):
    kind: typing.Literal["Liquidate"]


class MarginCalcJSON(typing.TypedDict):
    kind: typing.Literal["MarginCalc"]


class UpdateTwapJSON(typing.TypedDict):
    kind: typing.Literal["UpdateTwap"]


class UpdateAMMCurveJSON(typing.TypedDict):
    kind: typing.Literal["UpdateAMMCurve"]


@dataclass
class UpdateFunding:
    discriminator: typing.ClassVar = 0
    kind: typing.ClassVar = "UpdateFunding"

    @classmethod
    def to_json(cls) -> UpdateFundingJSON:
        return UpdateFundingJSON(
            kind="UpdateFunding",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "UpdateFunding": {},
        }


@dataclass
class SettlePnl:
    discriminator: typing.ClassVar = 1
    kind: typing.ClassVar = "SettlePnl"

    @classmethod
    def to_json(cls) -> SettlePnlJSON:
        return SettlePnlJSON(
            kind="SettlePnl",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "SettlePnl": {},
        }


@dataclass
class TriggerOrder:
    discriminator: typing.ClassVar = 2
    kind: typing.ClassVar = "TriggerOrder"

    @classmethod
    def to_json(cls) -> TriggerOrderJSON:
        return TriggerOrderJSON(
            kind="TriggerOrder",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "TriggerOrder": {},
        }


@dataclass
class FillOrderMatch:
    discriminator: typing.ClassVar = 3
    kind: typing.ClassVar = "FillOrderMatch"

    @classmethod
    def to_json(cls) -> FillOrderMatchJSON:
        return FillOrderMatchJSON(
            kind="FillOrderMatch",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "FillOrderMatch": {},
        }


@dataclass
class FillOrderAmm:
    discriminator: typing.ClassVar = 4
    kind: typing.ClassVar = "FillOrderAmm"

    @classmethod
    def to_json(cls) -> FillOrderAmmJSON:
        return FillOrderAmmJSON(
            kind="FillOrderAmm",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "FillOrderAmm": {},
        }


@dataclass
class Liquidate:
    discriminator: typing.ClassVar = 5
    kind: typing.ClassVar = "Liquidate"

    @classmethod
    def to_json(cls) -> LiquidateJSON:
        return LiquidateJSON(
            kind="Liquidate",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Liquidate": {},
        }


@dataclass
class MarginCalc:
    discriminator: typing.ClassVar = 6
    kind: typing.ClassVar = "MarginCalc"

    @classmethod
    def to_json(cls) -> MarginCalcJSON:
        return MarginCalcJSON(
            kind="MarginCalc",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "MarginCalc": {},
        }


@dataclass
class UpdateTwap:
    discriminator: typing.ClassVar = 7
    kind: typing.ClassVar = "UpdateTwap"

    @classmethod
    def to_json(cls) -> UpdateTwapJSON:
        return UpdateTwapJSON(
            kind="UpdateTwap",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "UpdateTwap": {},
        }


@dataclass
class UpdateAMMCurve:
    discriminator: typing.ClassVar = 8
    kind: typing.ClassVar = "UpdateAMMCurve"

    @classmethod
    def to_json(cls) -> UpdateAMMCurveJSON:
        return UpdateAMMCurveJSON(
            kind="UpdateAMMCurve",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "UpdateAMMCurve": {},
        }


DriftActionKind = typing.Union[
    UpdateFunding,
    SettlePnl,
    TriggerOrder,
    FillOrderMatch,
    FillOrderAmm,
    Liquidate,
    MarginCalc,
    UpdateTwap,
    UpdateAMMCurve,
]
DriftActionJSON = typing.Union[
    UpdateFundingJSON,
    SettlePnlJSON,
    TriggerOrderJSON,
    FillOrderMatchJSON,
    FillOrderAmmJSON,
    LiquidateJSON,
    MarginCalcJSON,
    UpdateTwapJSON,
    UpdateAMMCurveJSON,
]


def from_decoded(obj: dict) -> DriftActionKind:
    if not isinstance(obj, dict):
        raise ValueError("Invalid enum object")
    if "UpdateFunding" in obj:
        return UpdateFunding()
    if "SettlePnl" in obj:
        return SettlePnl()
    if "TriggerOrder" in obj:
        return TriggerOrder()
    if "FillOrderMatch" in obj:
        return FillOrderMatch()
    if "FillOrderAmm" in obj:
        return FillOrderAmm()
    if "Liquidate" in obj:
        return Liquidate()
    if "MarginCalc" in obj:
        return MarginCalc()
    if "UpdateTwap" in obj:
        return UpdateTwap()
    if "UpdateAMMCurve" in obj:
        return UpdateAMMCurve()
    raise ValueError("Invalid enum object")


def from_json(obj: DriftActionJSON) -> DriftActionKind:
    if obj["kind"] == "UpdateFunding":
        return UpdateFunding()
    if obj["kind"] == "SettlePnl":
        return SettlePnl()
    if obj["kind"] == "TriggerOrder":
        return TriggerOrder()
    if obj["kind"] == "FillOrderMatch":
        return FillOrderMatch()
    if obj["kind"] == "FillOrderAmm":
        return FillOrderAmm()
    if obj["kind"] == "Liquidate":
        return Liquidate()
    if obj["kind"] == "MarginCalc":
        return MarginCalc()
    if obj["kind"] == "UpdateTwap":
        return UpdateTwap()
    if obj["kind"] == "UpdateAMMCurve":
        return UpdateAMMCurve()
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen(
    "UpdateFunding" / borsh.CStruct(),
    "SettlePnl" / borsh.CStruct(),
    "TriggerOrder" / borsh.CStruct(),
    "FillOrderMatch" / borsh.CStruct(),
    "FillOrderAmm" / borsh.CStruct(),
    "Liquidate" / borsh.CStruct(),
    "MarginCalc" / borsh.CStruct(),
    "UpdateTwap" / borsh.CStruct(),
    "UpdateAMMCurve" / borsh.CStruct(),
)
