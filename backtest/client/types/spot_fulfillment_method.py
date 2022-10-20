from __future__ import annotations
import typing
from dataclasses import dataclass
from anchorpy.borsh_extension import EnumForCodegen
import borsh_construct as borsh


class SerumV3JSON(typing.TypedDict):
    kind: typing.Literal["SerumV3"]


class MatchJSON(typing.TypedDict):
    kind: typing.Literal["Match"]


@dataclass
class SerumV3:
    discriminator: typing.ClassVar = 0
    kind: typing.ClassVar = "SerumV3"

    @classmethod
    def to_json(cls) -> SerumV3JSON:
        return SerumV3JSON(
            kind="SerumV3",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "SerumV3": {},
        }


@dataclass
class Match:
    discriminator: typing.ClassVar = 1
    kind: typing.ClassVar = "Match"

    @classmethod
    def to_json(cls) -> MatchJSON:
        return MatchJSON(
            kind="Match",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Match": {},
        }


SpotFulfillmentMethodKind = typing.Union[SerumV3, Match]
SpotFulfillmentMethodJSON = typing.Union[SerumV3JSON, MatchJSON]


def from_decoded(obj: dict) -> SpotFulfillmentMethodKind:
    if not isinstance(obj, dict):
        raise ValueError("Invalid enum object")
    if "SerumV3" in obj:
        return SerumV3()
    if "Match" in obj:
        return Match()
    raise ValueError("Invalid enum object")


def from_json(obj: SpotFulfillmentMethodJSON) -> SpotFulfillmentMethodKind:
    if obj["kind"] == "SerumV3":
        return SerumV3()
    if obj["kind"] == "Match":
        return Match()
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen("SerumV3" / borsh.CStruct(), "Match" / borsh.CStruct())
