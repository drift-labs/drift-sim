from __future__ import annotations
import typing
from dataclasses import dataclass
from anchorpy.borsh_extension import EnumForCodegen
import borsh_construct as borsh


class FundingPeriodJSON(typing.TypedDict):
    kind: typing.Literal["FundingPeriod"]


class FiveMinJSON(typing.TypedDict):
    kind: typing.Literal["FiveMin"]


@dataclass
class FundingPeriod:
    discriminator: typing.ClassVar = 0
    kind: typing.ClassVar = "FundingPeriod"

    @classmethod
    def to_json(cls) -> FundingPeriodJSON:
        return FundingPeriodJSON(
            kind="FundingPeriod",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "FundingPeriod": {},
        }


@dataclass
class FiveMin:
    discriminator: typing.ClassVar = 1
    kind: typing.ClassVar = "FiveMin"

    @classmethod
    def to_json(cls) -> FiveMinJSON:
        return FiveMinJSON(
            kind="FiveMin",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "FiveMin": {},
        }


TwapPeriodKind = typing.Union[FundingPeriod, FiveMin]
TwapPeriodJSON = typing.Union[FundingPeriodJSON, FiveMinJSON]


def from_decoded(obj: dict) -> TwapPeriodKind:
    if not isinstance(obj, dict):
        raise ValueError("Invalid enum object")
    if "FundingPeriod" in obj:
        return FundingPeriod()
    if "FiveMin" in obj:
        return FiveMin()
    raise ValueError("Invalid enum object")


def from_json(obj: TwapPeriodJSON) -> TwapPeriodKind:
    if obj["kind"] == "FundingPeriod":
        return FundingPeriod()
    if obj["kind"] == "FiveMin":
        return FiveMin()
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen("FundingPeriod" / borsh.CStruct(), "FiveMin" / borsh.CStruct())
