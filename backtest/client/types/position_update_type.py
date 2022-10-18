from __future__ import annotations
import typing
from dataclasses import dataclass
from anchorpy.borsh_extension import EnumForCodegen
import borsh_construct as borsh


class OpenJSON(typing.TypedDict):
    kind: typing.Literal["Open"]


class IncreaseJSON(typing.TypedDict):
    kind: typing.Literal["Increase"]


class ReduceJSON(typing.TypedDict):
    kind: typing.Literal["Reduce"]


class CloseJSON(typing.TypedDict):
    kind: typing.Literal["Close"]


class FlipJSON(typing.TypedDict):
    kind: typing.Literal["Flip"]


@dataclass
class Open:
    discriminator: typing.ClassVar = 0
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
class Increase:
    discriminator: typing.ClassVar = 1
    kind: typing.ClassVar = "Increase"

    @classmethod
    def to_json(cls) -> IncreaseJSON:
        return IncreaseJSON(
            kind="Increase",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Increase": {},
        }


@dataclass
class Reduce:
    discriminator: typing.ClassVar = 2
    kind: typing.ClassVar = "Reduce"

    @classmethod
    def to_json(cls) -> ReduceJSON:
        return ReduceJSON(
            kind="Reduce",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Reduce": {},
        }


@dataclass
class Close:
    discriminator: typing.ClassVar = 3
    kind: typing.ClassVar = "Close"

    @classmethod
    def to_json(cls) -> CloseJSON:
        return CloseJSON(
            kind="Close",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Close": {},
        }


@dataclass
class Flip:
    discriminator: typing.ClassVar = 4
    kind: typing.ClassVar = "Flip"

    @classmethod
    def to_json(cls) -> FlipJSON:
        return FlipJSON(
            kind="Flip",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Flip": {},
        }


PositionUpdateTypeKind = typing.Union[Open, Increase, Reduce, Close, Flip]
PositionUpdateTypeJSON = typing.Union[
    OpenJSON, IncreaseJSON, ReduceJSON, CloseJSON, FlipJSON
]


def from_decoded(obj: dict) -> PositionUpdateTypeKind:
    if not isinstance(obj, dict):
        raise ValueError("Invalid enum object")
    if "Open" in obj:
        return Open()
    if "Increase" in obj:
        return Increase()
    if "Reduce" in obj:
        return Reduce()
    if "Close" in obj:
        return Close()
    if "Flip" in obj:
        return Flip()
    raise ValueError("Invalid enum object")


def from_json(obj: PositionUpdateTypeJSON) -> PositionUpdateTypeKind:
    if obj["kind"] == "Open":
        return Open()
    if obj["kind"] == "Increase":
        return Increase()
    if obj["kind"] == "Reduce":
        return Reduce()
    if obj["kind"] == "Close":
        return Close()
    if obj["kind"] == "Flip":
        return Flip()
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen(
    "Open" / borsh.CStruct(),
    "Increase" / borsh.CStruct(),
    "Reduce" / borsh.CStruct(),
    "Close" / borsh.CStruct(),
    "Flip" / borsh.CStruct(),
)
