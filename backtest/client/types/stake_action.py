from __future__ import annotations
import typing
from dataclasses import dataclass
from anchorpy.borsh_extension import EnumForCodegen
import borsh_construct as borsh


class StakeJSON(typing.TypedDict):
    kind: typing.Literal["Stake"]


class UnstakeRequestJSON(typing.TypedDict):
    kind: typing.Literal["UnstakeRequest"]


class UnstakeCancelRequestJSON(typing.TypedDict):
    kind: typing.Literal["UnstakeCancelRequest"]


class UnstakeJSON(typing.TypedDict):
    kind: typing.Literal["Unstake"]


@dataclass
class Stake:
    discriminator: typing.ClassVar = 0
    kind: typing.ClassVar = "Stake"

    @classmethod
    def to_json(cls) -> StakeJSON:
        return StakeJSON(
            kind="Stake",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Stake": {},
        }


@dataclass
class UnstakeRequest:
    discriminator: typing.ClassVar = 1
    kind: typing.ClassVar = "UnstakeRequest"

    @classmethod
    def to_json(cls) -> UnstakeRequestJSON:
        return UnstakeRequestJSON(
            kind="UnstakeRequest",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "UnstakeRequest": {},
        }


@dataclass
class UnstakeCancelRequest:
    discriminator: typing.ClassVar = 2
    kind: typing.ClassVar = "UnstakeCancelRequest"

    @classmethod
    def to_json(cls) -> UnstakeCancelRequestJSON:
        return UnstakeCancelRequestJSON(
            kind="UnstakeCancelRequest",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "UnstakeCancelRequest": {},
        }


@dataclass
class Unstake:
    discriminator: typing.ClassVar = 3
    kind: typing.ClassVar = "Unstake"

    @classmethod
    def to_json(cls) -> UnstakeJSON:
        return UnstakeJSON(
            kind="Unstake",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Unstake": {},
        }


StakeActionKind = typing.Union[Stake, UnstakeRequest, UnstakeCancelRequest, Unstake]
StakeActionJSON = typing.Union[
    StakeJSON, UnstakeRequestJSON, UnstakeCancelRequestJSON, UnstakeJSON
]


def from_decoded(obj: dict) -> StakeActionKind:
    if not isinstance(obj, dict):
        raise ValueError("Invalid enum object")
    if "Stake" in obj:
        return Stake()
    if "UnstakeRequest" in obj:
        return UnstakeRequest()
    if "UnstakeCancelRequest" in obj:
        return UnstakeCancelRequest()
    if "Unstake" in obj:
        return Unstake()
    raise ValueError("Invalid enum object")


def from_json(obj: StakeActionJSON) -> StakeActionKind:
    if obj["kind"] == "Stake":
        return Stake()
    if obj["kind"] == "UnstakeRequest":
        return UnstakeRequest()
    if obj["kind"] == "UnstakeCancelRequest":
        return UnstakeCancelRequest()
    if obj["kind"] == "Unstake":
        return Unstake()
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen(
    "Stake" / borsh.CStruct(),
    "UnstakeRequest" / borsh.CStruct(),
    "UnstakeCancelRequest" / borsh.CStruct(),
    "Unstake" / borsh.CStruct(),
)
