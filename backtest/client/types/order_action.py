from __future__ import annotations
import typing
from dataclasses import dataclass
from anchorpy.borsh_extension import EnumForCodegen
import borsh_construct as borsh


class PlaceJSON(typing.TypedDict):
    kind: typing.Literal["Place"]


class CancelJSON(typing.TypedDict):
    kind: typing.Literal["Cancel"]


class FillJSON(typing.TypedDict):
    kind: typing.Literal["Fill"]


class TriggerJSON(typing.TypedDict):
    kind: typing.Literal["Trigger"]


class ExpireJSON(typing.TypedDict):
    kind: typing.Literal["Expire"]


@dataclass
class Place:
    discriminator: typing.ClassVar = 0
    kind: typing.ClassVar = "Place"

    @classmethod
    def to_json(cls) -> PlaceJSON:
        return PlaceJSON(
            kind="Place",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Place": {},
        }


@dataclass
class Cancel:
    discriminator: typing.ClassVar = 1
    kind: typing.ClassVar = "Cancel"

    @classmethod
    def to_json(cls) -> CancelJSON:
        return CancelJSON(
            kind="Cancel",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Cancel": {},
        }


@dataclass
class Fill:
    discriminator: typing.ClassVar = 2
    kind: typing.ClassVar = "Fill"

    @classmethod
    def to_json(cls) -> FillJSON:
        return FillJSON(
            kind="Fill",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Fill": {},
        }


@dataclass
class Trigger:
    discriminator: typing.ClassVar = 3
    kind: typing.ClassVar = "Trigger"

    @classmethod
    def to_json(cls) -> TriggerJSON:
        return TriggerJSON(
            kind="Trigger",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Trigger": {},
        }


@dataclass
class Expire:
    discriminator: typing.ClassVar = 4
    kind: typing.ClassVar = "Expire"

    @classmethod
    def to_json(cls) -> ExpireJSON:
        return ExpireJSON(
            kind="Expire",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Expire": {},
        }


OrderActionKind = typing.Union[Place, Cancel, Fill, Trigger, Expire]
OrderActionJSON = typing.Union[PlaceJSON, CancelJSON, FillJSON, TriggerJSON, ExpireJSON]


def from_decoded(obj: dict) -> OrderActionKind:
    if not isinstance(obj, dict):
        raise ValueError("Invalid enum object")
    if "Place" in obj:
        return Place()
    if "Cancel" in obj:
        return Cancel()
    if "Fill" in obj:
        return Fill()
    if "Trigger" in obj:
        return Trigger()
    if "Expire" in obj:
        return Expire()
    raise ValueError("Invalid enum object")


def from_json(obj: OrderActionJSON) -> OrderActionKind:
    if obj["kind"] == "Place":
        return Place()
    if obj["kind"] == "Cancel":
        return Cancel()
    if obj["kind"] == "Fill":
        return Fill()
    if obj["kind"] == "Trigger":
        return Trigger()
    if obj["kind"] == "Expire":
        return Expire()
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen(
    "Place" / borsh.CStruct(),
    "Cancel" / borsh.CStruct(),
    "Fill" / borsh.CStruct(),
    "Trigger" / borsh.CStruct(),
    "Expire" / borsh.CStruct(),
)
