from __future__ import annotations
import typing
from dataclasses import dataclass
from anchorpy.borsh_extension import EnumForCodegen
import borsh_construct as borsh


class SpotJSON(typing.TypedDict):
    kind: typing.Literal["Spot"]


class PerpJSON(typing.TypedDict):
    kind: typing.Literal["Perp"]


@dataclass
class Spot:
    discriminator: typing.ClassVar = 0
    kind: typing.ClassVar = "Spot"

    @classmethod
    def to_json(cls) -> SpotJSON:
        return SpotJSON(
            kind="Spot",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Spot": {},
        }


@dataclass
class Perp:
    discriminator: typing.ClassVar = 1
    kind: typing.ClassVar = "Perp"

    @classmethod
    def to_json(cls) -> PerpJSON:
        return PerpJSON(
            kind="Perp",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Perp": {},
        }


MarketTypeKind = typing.Union[Spot, Perp]
MarketTypeJSON = typing.Union[SpotJSON, PerpJSON]


def from_decoded(obj: dict) -> MarketTypeKind:
    if not isinstance(obj, dict):
        raise ValueError("Invalid enum object")
    if "Spot" in obj:
        return Spot()
    if "Perp" in obj:
        return Perp()
    raise ValueError("Invalid enum object")


def from_json(obj: MarketTypeJSON) -> MarketTypeKind:
    if obj["kind"] == "Spot":
        return Spot()
    if obj["kind"] == "Perp":
        return Perp()
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen("Spot" / borsh.CStruct(), "Perp" / borsh.CStruct())
