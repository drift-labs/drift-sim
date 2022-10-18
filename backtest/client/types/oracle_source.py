from __future__ import annotations
import typing
from dataclasses import dataclass
from anchorpy.borsh_extension import EnumForCodegen
import borsh_construct as borsh


class PythJSON(typing.TypedDict):
    kind: typing.Literal["Pyth"]


class SwitchboardJSON(typing.TypedDict):
    kind: typing.Literal["Switchboard"]


class QuoteAssetJSON(typing.TypedDict):
    kind: typing.Literal["QuoteAsset"]


@dataclass
class Pyth:
    discriminator: typing.ClassVar = 0
    kind: typing.ClassVar = "Pyth"

    @classmethod
    def to_json(cls) -> PythJSON:
        return PythJSON(
            kind="Pyth",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Pyth": {},
        }


@dataclass
class Switchboard:
    discriminator: typing.ClassVar = 1
    kind: typing.ClassVar = "Switchboard"

    @classmethod
    def to_json(cls) -> SwitchboardJSON:
        return SwitchboardJSON(
            kind="Switchboard",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Switchboard": {},
        }


@dataclass
class QuoteAsset:
    discriminator: typing.ClassVar = 2
    kind: typing.ClassVar = "QuoteAsset"

    @classmethod
    def to_json(cls) -> QuoteAssetJSON:
        return QuoteAssetJSON(
            kind="QuoteAsset",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "QuoteAsset": {},
        }


OracleSourceKind = typing.Union[Pyth, Switchboard, QuoteAsset]
OracleSourceJSON = typing.Union[PythJSON, SwitchboardJSON, QuoteAssetJSON]


def from_decoded(obj: dict) -> OracleSourceKind:
    if not isinstance(obj, dict):
        raise ValueError("Invalid enum object")
    if "Pyth" in obj:
        return Pyth()
    if "Switchboard" in obj:
        return Switchboard()
    if "QuoteAsset" in obj:
        return QuoteAsset()
    raise ValueError("Invalid enum object")


def from_json(obj: OracleSourceJSON) -> OracleSourceKind:
    if obj["kind"] == "Pyth":
        return Pyth()
    if obj["kind"] == "Switchboard":
        return Switchboard()
    if obj["kind"] == "QuoteAsset":
        return QuoteAsset()
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen(
    "Pyth" / borsh.CStruct(),
    "Switchboard" / borsh.CStruct(),
    "QuoteAsset" / borsh.CStruct(),
)
