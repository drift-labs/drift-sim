from __future__ import annotations
import typing
from dataclasses import dataclass
from anchorpy.borsh_extension import EnumForCodegen
import borsh_construct as borsh


class SerumV3JSON(typing.TypedDict):
    kind: typing.Literal["SerumV3"]


class NoneJSON(typing.TypedDict):
    kind: typing.Literal["None"]


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
class None_:
    discriminator: typing.ClassVar = 1
    kind: typing.ClassVar = "None"

    @classmethod
    def to_json(cls) -> NoneJSON:
        return NoneJSON(
            kind="None",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "None": {},
        }


SpotFulfillmentTypeKind = typing.Union[SerumV3, None_]
SpotFulfillmentTypeJSON = typing.Union[SerumV3JSON, NoneJSON]


def from_decoded(obj: dict) -> SpotFulfillmentTypeKind:
    if not isinstance(obj, dict):
        raise ValueError("Invalid enum object")
    if "SerumV3" in obj:
        return SerumV3()
    if "None" in obj:
        return None_()
    raise ValueError("Invalid enum object")


def from_json(obj: SpotFulfillmentTypeJSON) -> SpotFulfillmentTypeKind:
    if obj["kind"] == "SerumV3":
        return SerumV3()
    if obj["kind"] == "None":
        return None_()
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen("SerumV3" / borsh.CStruct(), "None" / borsh.CStruct())
