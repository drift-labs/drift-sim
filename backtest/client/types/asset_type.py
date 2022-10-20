from __future__ import annotations
import typing
from dataclasses import dataclass
from anchorpy.borsh_extension import EnumForCodegen
import borsh_construct as borsh


class BaseJSON(typing.TypedDict):
    kind: typing.Literal["Base"]


class QuoteJSON(typing.TypedDict):
    kind: typing.Literal["Quote"]


@dataclass
class Base:
    discriminator: typing.ClassVar = 0
    kind: typing.ClassVar = "Base"

    @classmethod
    def to_json(cls) -> BaseJSON:
        return BaseJSON(
            kind="Base",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Base": {},
        }


@dataclass
class Quote:
    discriminator: typing.ClassVar = 1
    kind: typing.ClassVar = "Quote"

    @classmethod
    def to_json(cls) -> QuoteJSON:
        return QuoteJSON(
            kind="Quote",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Quote": {},
        }


AssetTypeKind = typing.Union[Base, Quote]
AssetTypeJSON = typing.Union[BaseJSON, QuoteJSON]


def from_decoded(obj: dict) -> AssetTypeKind:
    if not isinstance(obj, dict):
        raise ValueError("Invalid enum object")
    if "Base" in obj:
        return Base()
    if "Quote" in obj:
        return Quote()
    raise ValueError("Invalid enum object")


def from_json(obj: AssetTypeJSON) -> AssetTypeKind:
    if obj["kind"] == "Base":
        return Base()
    if obj["kind"] == "Quote":
        return Quote()
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen("Base" / borsh.CStruct(), "Quote" / borsh.CStruct())
