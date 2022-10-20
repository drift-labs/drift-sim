from __future__ import annotations
import typing
from dataclasses import dataclass
from anchorpy.borsh_extension import EnumForCodegen
import borsh_construct as borsh


class AddJSON(typing.TypedDict):
    kind: typing.Literal["Add"]


class RemoveJSON(typing.TypedDict):
    kind: typing.Literal["Remove"]


@dataclass
class Add:
    discriminator: typing.ClassVar = 0
    kind: typing.ClassVar = "Add"

    @classmethod
    def to_json(cls) -> AddJSON:
        return AddJSON(
            kind="Add",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Add": {},
        }


@dataclass
class Remove:
    discriminator: typing.ClassVar = 1
    kind: typing.ClassVar = "Remove"

    @classmethod
    def to_json(cls) -> RemoveJSON:
        return RemoveJSON(
            kind="Remove",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Remove": {},
        }


SwapDirectionKind = typing.Union[Add, Remove]
SwapDirectionJSON = typing.Union[AddJSON, RemoveJSON]


def from_decoded(obj: dict) -> SwapDirectionKind:
    if not isinstance(obj, dict):
        raise ValueError("Invalid enum object")
    if "Add" in obj:
        return Add()
    if "Remove" in obj:
        return Remove()
    raise ValueError("Invalid enum object")


def from_json(obj: SwapDirectionJSON) -> SwapDirectionKind:
    if obj["kind"] == "Add":
        return Add()
    if obj["kind"] == "Remove":
        return Remove()
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen("Add" / borsh.CStruct(), "Remove" / borsh.CStruct())
