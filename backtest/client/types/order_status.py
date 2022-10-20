from __future__ import annotations
import typing
from dataclasses import dataclass
from anchorpy.borsh_extension import EnumForCodegen
import borsh_construct as borsh


class InitJSON(typing.TypedDict):
    kind: typing.Literal["Init"]


class OpenJSON(typing.TypedDict):
    kind: typing.Literal["Open"]


class FilledJSON(typing.TypedDict):
    kind: typing.Literal["Filled"]


class CanceledJSON(typing.TypedDict):
    kind: typing.Literal["Canceled"]


@dataclass
class Init:
    discriminator: typing.ClassVar = 0
    kind: typing.ClassVar = "Init"

    @classmethod
    def to_json(cls) -> InitJSON:
        return InitJSON(
            kind="Init",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Init": {},
        }


@dataclass
class Open:
    discriminator: typing.ClassVar = 1
    kind: typing.ClassVar = "Open"

    @classmethod
    def to_json(cls) -> OpenJSON:
        return OpenJSON(
            kind="Open",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Open": {},
        }


@dataclass
class Filled:
    discriminator: typing.ClassVar = 2
    kind: typing.ClassVar = "Filled"

    @classmethod
    def to_json(cls) -> FilledJSON:
        return FilledJSON(
            kind="Filled",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Filled": {},
        }


@dataclass
class Canceled:
    discriminator: typing.ClassVar = 3
    kind: typing.ClassVar = "Canceled"

    @classmethod
    def to_json(cls) -> CanceledJSON:
        return CanceledJSON(
            kind="Canceled",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Canceled": {},
        }


OrderStatusKind = typing.Union[Init, Open, Filled, Canceled]
OrderStatusJSON = typing.Union[InitJSON, OpenJSON, FilledJSON, CanceledJSON]


def from_decoded(obj: dict) -> OrderStatusKind:
    if not isinstance(obj, dict):
        raise ValueError("Invalid enum object")
    if "Init" in obj:
        return Init()
    if "Open" in obj:
        return Open()
    if "Filled" in obj:
        return Filled()
    if "Canceled" in obj:
        return Canceled()
    raise ValueError("Invalid enum object")


def from_json(obj: OrderStatusJSON) -> OrderStatusKind:
    if obj["kind"] == "Init":
        return Init()
    if obj["kind"] == "Open":
        return Open()
    if obj["kind"] == "Filled":
        return Filled()
    if obj["kind"] == "Canceled":
        return Canceled()
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen(
    "Init" / borsh.CStruct(),
    "Open" / borsh.CStruct(),
    "Filled" / borsh.CStruct(),
    "Canceled" / borsh.CStruct(),
)
