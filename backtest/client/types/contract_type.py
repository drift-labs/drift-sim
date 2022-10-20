from __future__ import annotations
import typing
from dataclasses import dataclass
from anchorpy.borsh_extension import EnumForCodegen
import borsh_construct as borsh


class PerpetualJSON(typing.TypedDict):
    kind: typing.Literal["Perpetual"]


class FutureJSON(typing.TypedDict):
    kind: typing.Literal["Future"]


@dataclass
class Perpetual:
    discriminator: typing.ClassVar = 0
    kind: typing.ClassVar = "Perpetual"

    @classmethod
    def to_json(cls) -> PerpetualJSON:
        return PerpetualJSON(
            kind="Perpetual",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Perpetual": {},
        }


@dataclass
class Future:
    discriminator: typing.ClassVar = 1
    kind: typing.ClassVar = "Future"

    @classmethod
    def to_json(cls) -> FutureJSON:
        return FutureJSON(
            kind="Future",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Future": {},
        }


ContractTypeKind = typing.Union[Perpetual, Future]
ContractTypeJSON = typing.Union[PerpetualJSON, FutureJSON]


def from_decoded(obj: dict) -> ContractTypeKind:
    if not isinstance(obj, dict):
        raise ValueError("Invalid enum object")
    if "Perpetual" in obj:
        return Perpetual()
    if "Future" in obj:
        return Future()
    raise ValueError("Invalid enum object")


def from_json(obj: ContractTypeJSON) -> ContractTypeKind:
    if obj["kind"] == "Perpetual":
        return Perpetual()
    if obj["kind"] == "Future":
        return Future()
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen("Perpetual" / borsh.CStruct(), "Future" / borsh.CStruct())
