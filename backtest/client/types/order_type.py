from __future__ import annotations
import typing
from dataclasses import dataclass
from anchorpy.borsh_extension import EnumForCodegen
import borsh_construct as borsh


class MarketJSON(typing.TypedDict):
    kind: typing.Literal["Market"]


class LimitJSON(typing.TypedDict):
    kind: typing.Literal["Limit"]


class TriggerMarketJSON(typing.TypedDict):
    kind: typing.Literal["TriggerMarket"]


class TriggerLimitJSON(typing.TypedDict):
    kind: typing.Literal["TriggerLimit"]


@dataclass
class Market:
    discriminator: typing.ClassVar = 0
    kind: typing.ClassVar = "Market"

    @classmethod
    def to_json(cls) -> MarketJSON:
        return MarketJSON(
            kind="Market",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Market": {},
        }


@dataclass
class Limit:
    discriminator: typing.ClassVar = 1
    kind: typing.ClassVar = "Limit"

    @classmethod
    def to_json(cls) -> LimitJSON:
        return LimitJSON(
            kind="Limit",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Limit": {},
        }


@dataclass
class TriggerMarket:
    discriminator: typing.ClassVar = 2
    kind: typing.ClassVar = "TriggerMarket"

    @classmethod
    def to_json(cls) -> TriggerMarketJSON:
        return TriggerMarketJSON(
            kind="TriggerMarket",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "TriggerMarket": {},
        }


@dataclass
class TriggerLimit:
    discriminator: typing.ClassVar = 3
    kind: typing.ClassVar = "TriggerLimit"

    @classmethod
    def to_json(cls) -> TriggerLimitJSON:
        return TriggerLimitJSON(
            kind="TriggerLimit",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "TriggerLimit": {},
        }


OrderTypeKind = typing.Union[Market, Limit, TriggerMarket, TriggerLimit]
OrderTypeJSON = typing.Union[MarketJSON, LimitJSON, TriggerMarketJSON, TriggerLimitJSON]


def from_decoded(obj: dict) -> OrderTypeKind:
    if not isinstance(obj, dict):
        raise ValueError("Invalid enum object")
    if "Market" in obj:
        return Market()
    if "Limit" in obj:
        return Limit()
    if "TriggerMarket" in obj:
        return TriggerMarket()
    if "TriggerLimit" in obj:
        return TriggerLimit()
    raise ValueError("Invalid enum object")


def from_json(obj: OrderTypeJSON) -> OrderTypeKind:
    if obj["kind"] == "Market":
        return Market()
    if obj["kind"] == "Limit":
        return Limit()
    if obj["kind"] == "TriggerMarket":
        return TriggerMarket()
    if obj["kind"] == "TriggerLimit":
        return TriggerLimit()
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen(
    "Market" / borsh.CStruct(),
    "Limit" / borsh.CStruct(),
    "TriggerMarket" / borsh.CStruct(),
    "TriggerLimit" / borsh.CStruct(),
)
