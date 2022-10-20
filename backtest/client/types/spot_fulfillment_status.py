from __future__ import annotations
import typing
from dataclasses import dataclass
from anchorpy.borsh_extension import EnumForCodegen
import borsh_construct as borsh


class EnabledJSON(typing.TypedDict):
    kind: typing.Literal["Enabled"]


class DisabledJSON(typing.TypedDict):
    kind: typing.Literal["Disabled"]


@dataclass
class Enabled:
    discriminator: typing.ClassVar = 0
    kind: typing.ClassVar = "Enabled"

    @classmethod
    def to_json(cls) -> EnabledJSON:
        return EnabledJSON(
            kind="Enabled",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Enabled": {},
        }


@dataclass
class Disabled:
    discriminator: typing.ClassVar = 1
    kind: typing.ClassVar = "Disabled"

    @classmethod
    def to_json(cls) -> DisabledJSON:
        return DisabledJSON(
            kind="Disabled",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Disabled": {},
        }


SpotFulfillmentStatusKind = typing.Union[Enabled, Disabled]
SpotFulfillmentStatusJSON = typing.Union[EnabledJSON, DisabledJSON]


def from_decoded(obj: dict) -> SpotFulfillmentStatusKind:
    if not isinstance(obj, dict):
        raise ValueError("Invalid enum object")
    if "Enabled" in obj:
        return Enabled()
    if "Disabled" in obj:
        return Disabled()
    raise ValueError("Invalid enum object")


def from_json(obj: SpotFulfillmentStatusJSON) -> SpotFulfillmentStatusKind:
    if obj["kind"] == "Enabled":
        return Enabled()
    if obj["kind"] == "Disabled":
        return Disabled()
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen("Enabled" / borsh.CStruct(), "Disabled" / borsh.CStruct())
