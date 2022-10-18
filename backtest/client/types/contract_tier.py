from __future__ import annotations
import typing
from dataclasses import dataclass
from anchorpy.borsh_extension import EnumForCodegen
import borsh_construct as borsh


class AJSON(typing.TypedDict):
    kind: typing.Literal["A"]


class BJSON(typing.TypedDict):
    kind: typing.Literal["B"]


class CJSON(typing.TypedDict):
    kind: typing.Literal["C"]


class SpeculativeJSON(typing.TypedDict):
    kind: typing.Literal["Speculative"]


@dataclass
class A:
    discriminator: typing.ClassVar = 0
    kind: typing.ClassVar = "A"

    @classmethod
    def to_json(cls) -> AJSON:
        return AJSON(
            kind="A",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "A": {},
        }


@dataclass
class B:
    discriminator: typing.ClassVar = 1
    kind: typing.ClassVar = "B"

    @classmethod
    def to_json(cls) -> BJSON:
        return BJSON(
            kind="B",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "B": {},
        }


@dataclass
class C:
    discriminator: typing.ClassVar = 2
    kind: typing.ClassVar = "C"

    @classmethod
    def to_json(cls) -> CJSON:
        return CJSON(
            kind="C",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "C": {},
        }


@dataclass
class Speculative:
    discriminator: typing.ClassVar = 3
    kind: typing.ClassVar = "Speculative"

    @classmethod
    def to_json(cls) -> SpeculativeJSON:
        return SpeculativeJSON(
            kind="Speculative",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Speculative": {},
        }


ContractTierKind = typing.Union[A, B, C, Speculative]
ContractTierJSON = typing.Union[AJSON, BJSON, CJSON, SpeculativeJSON]


def from_decoded(obj: dict) -> ContractTierKind:
    if not isinstance(obj, dict):
        raise ValueError("Invalid enum object")
    if "A" in obj:
        return A()
    if "B" in obj:
        return B()
    if "C" in obj:
        return C()
    if "Speculative" in obj:
        return Speculative()
    raise ValueError("Invalid enum object")


def from_json(obj: ContractTierJSON) -> ContractTierKind:
    if obj["kind"] == "A":
        return A()
    if obj["kind"] == "B":
        return B()
    if obj["kind"] == "C":
        return C()
    if obj["kind"] == "Speculative":
        return Speculative()
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen(
    "A" / borsh.CStruct(),
    "B" / borsh.CStruct(),
    "C" / borsh.CStruct(),
    "Speculative" / borsh.CStruct(),
)
