from __future__ import annotations
import typing
from dataclasses import dataclass
from anchorpy.borsh_extension import EnumForCodegen
import borsh_construct as borsh


class AboveJSON(typing.TypedDict):
    kind: typing.Literal["Above"]


class BelowJSON(typing.TypedDict):
    kind: typing.Literal["Below"]


@dataclass
class Above:
    discriminator: typing.ClassVar = 0
    kind: typing.ClassVar = "Above"

    @classmethod
    def to_json(cls) -> AboveJSON:
        return AboveJSON(
            kind="Above",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Above": {},
        }


@dataclass
class Below:
    discriminator: typing.ClassVar = 1
    kind: typing.ClassVar = "Below"

    @classmethod
    def to_json(cls) -> BelowJSON:
        return BelowJSON(
            kind="Below",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Below": {},
        }


OrderTriggerConditionKind = typing.Union[Above, Below]
OrderTriggerConditionJSON = typing.Union[AboveJSON, BelowJSON]


def from_decoded(obj: dict) -> OrderTriggerConditionKind:
    if not isinstance(obj, dict):
        raise ValueError("Invalid enum object")
    if "Above" in obj:
        return Above()
    if "Below" in obj:
        return Below()
    raise ValueError("Invalid enum object")


def from_json(obj: OrderTriggerConditionJSON) -> OrderTriggerConditionKind:
    if obj["kind"] == "Above":
        return Above()
    if obj["kind"] == "Below":
        return Below()
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen("Above" / borsh.CStruct(), "Below" / borsh.CStruct())
