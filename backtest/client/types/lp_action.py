from __future__ import annotations
import typing
from dataclasses import dataclass
from anchorpy.borsh_extension import EnumForCodegen
import borsh_construct as borsh


class AddLiquidityJSON(typing.TypedDict):
    kind: typing.Literal["AddLiquidity"]


class RemoveLiquidityJSON(typing.TypedDict):
    kind: typing.Literal["RemoveLiquidity"]


class SettleLiquidityJSON(typing.TypedDict):
    kind: typing.Literal["SettleLiquidity"]


@dataclass
class AddLiquidity:
    discriminator: typing.ClassVar = 0
    kind: typing.ClassVar = "AddLiquidity"

    @classmethod
    def to_json(cls) -> AddLiquidityJSON:
        return AddLiquidityJSON(
            kind="AddLiquidity",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "AddLiquidity": {},
        }


@dataclass
class RemoveLiquidity:
    discriminator: typing.ClassVar = 1
    kind: typing.ClassVar = "RemoveLiquidity"

    @classmethod
    def to_json(cls) -> RemoveLiquidityJSON:
        return RemoveLiquidityJSON(
            kind="RemoveLiquidity",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "RemoveLiquidity": {},
        }


@dataclass
class SettleLiquidity:
    discriminator: typing.ClassVar = 2
    kind: typing.ClassVar = "SettleLiquidity"

    @classmethod
    def to_json(cls) -> SettleLiquidityJSON:
        return SettleLiquidityJSON(
            kind="SettleLiquidity",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "SettleLiquidity": {},
        }


LPActionKind = typing.Union[AddLiquidity, RemoveLiquidity, SettleLiquidity]
LPActionJSON = typing.Union[AddLiquidityJSON, RemoveLiquidityJSON, SettleLiquidityJSON]


def from_decoded(obj: dict) -> LPActionKind:
    if not isinstance(obj, dict):
        raise ValueError("Invalid enum object")
    if "AddLiquidity" in obj:
        return AddLiquidity()
    if "RemoveLiquidity" in obj:
        return RemoveLiquidity()
    if "SettleLiquidity" in obj:
        return SettleLiquidity()
    raise ValueError("Invalid enum object")


def from_json(obj: LPActionJSON) -> LPActionKind:
    if obj["kind"] == "AddLiquidity":
        return AddLiquidity()
    if obj["kind"] == "RemoveLiquidity":
        return RemoveLiquidity()
    if obj["kind"] == "SettleLiquidity":
        return SettleLiquidity()
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen(
    "AddLiquidity" / borsh.CStruct(),
    "RemoveLiquidity" / borsh.CStruct(),
    "SettleLiquidity" / borsh.CStruct(),
)
