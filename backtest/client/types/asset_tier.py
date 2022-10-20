from __future__ import annotations
import typing
from dataclasses import dataclass
from anchorpy.borsh_extension import EnumForCodegen
import borsh_construct as borsh


class CollateralJSON(typing.TypedDict):
    kind: typing.Literal["Collateral"]


class ProtectedJSON(typing.TypedDict):
    kind: typing.Literal["Protected"]


class CrossJSON(typing.TypedDict):
    kind: typing.Literal["Cross"]


class IsolatedJSON(typing.TypedDict):
    kind: typing.Literal["Isolated"]


class UnlistedJSON(typing.TypedDict):
    kind: typing.Literal["Unlisted"]


@dataclass
class Collateral:
    discriminator: typing.ClassVar = 0
    kind: typing.ClassVar = "Collateral"

    @classmethod
    def to_json(cls) -> CollateralJSON:
        return CollateralJSON(
            kind="Collateral",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Collateral": {},
        }


@dataclass
class Protected:
    discriminator: typing.ClassVar = 1
    kind: typing.ClassVar = "Protected"

    @classmethod
    def to_json(cls) -> ProtectedJSON:
        return ProtectedJSON(
            kind="Protected",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Protected": {},
        }


@dataclass
class Cross:
    discriminator: typing.ClassVar = 2
    kind: typing.ClassVar = "Cross"

    @classmethod
    def to_json(cls) -> CrossJSON:
        return CrossJSON(
            kind="Cross",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Cross": {},
        }


@dataclass
class Isolated:
    discriminator: typing.ClassVar = 3
    kind: typing.ClassVar = "Isolated"

    @classmethod
    def to_json(cls) -> IsolatedJSON:
        return IsolatedJSON(
            kind="Isolated",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Isolated": {},
        }


@dataclass
class Unlisted:
    discriminator: typing.ClassVar = 4
    kind: typing.ClassVar = "Unlisted"

    @classmethod
    def to_json(cls) -> UnlistedJSON:
        return UnlistedJSON(
            kind="Unlisted",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Unlisted": {},
        }


AssetTierKind = typing.Union[Collateral, Protected, Cross, Isolated, Unlisted]
AssetTierJSON = typing.Union[
    CollateralJSON, ProtectedJSON, CrossJSON, IsolatedJSON, UnlistedJSON
]


def from_decoded(obj: dict) -> AssetTierKind:
    if not isinstance(obj, dict):
        raise ValueError("Invalid enum object")
    if "Collateral" in obj:
        return Collateral()
    if "Protected" in obj:
        return Protected()
    if "Cross" in obj:
        return Cross()
    if "Isolated" in obj:
        return Isolated()
    if "Unlisted" in obj:
        return Unlisted()
    raise ValueError("Invalid enum object")


def from_json(obj: AssetTierJSON) -> AssetTierKind:
    if obj["kind"] == "Collateral":
        return Collateral()
    if obj["kind"] == "Protected":
        return Protected()
    if obj["kind"] == "Cross":
        return Cross()
    if obj["kind"] == "Isolated":
        return Isolated()
    if obj["kind"] == "Unlisted":
        return Unlisted()
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen(
    "Collateral" / borsh.CStruct(),
    "Protected" / borsh.CStruct(),
    "Cross" / borsh.CStruct(),
    "Isolated" / borsh.CStruct(),
    "Unlisted" / borsh.CStruct(),
)
