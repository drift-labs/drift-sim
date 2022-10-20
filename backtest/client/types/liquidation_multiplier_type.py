from __future__ import annotations
import typing
from dataclasses import dataclass
from anchorpy.borsh_extension import EnumForCodegen
import borsh_construct as borsh


class DiscountJSON(typing.TypedDict):
    kind: typing.Literal["Discount"]


class PremiumJSON(typing.TypedDict):
    kind: typing.Literal["Premium"]


@dataclass
class Discount:
    discriminator: typing.ClassVar = 0
    kind: typing.ClassVar = "Discount"

    @classmethod
    def to_json(cls) -> DiscountJSON:
        return DiscountJSON(
            kind="Discount",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Discount": {},
        }


@dataclass
class Premium:
    discriminator: typing.ClassVar = 1
    kind: typing.ClassVar = "Premium"

    @classmethod
    def to_json(cls) -> PremiumJSON:
        return PremiumJSON(
            kind="Premium",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Premium": {},
        }


LiquidationMultiplierTypeKind = typing.Union[Discount, Premium]
LiquidationMultiplierTypeJSON = typing.Union[DiscountJSON, PremiumJSON]


def from_decoded(obj: dict) -> LiquidationMultiplierTypeKind:
    if not isinstance(obj, dict):
        raise ValueError("Invalid enum object")
    if "Discount" in obj:
        return Discount()
    if "Premium" in obj:
        return Premium()
    raise ValueError("Invalid enum object")


def from_json(obj: LiquidationMultiplierTypeJSON) -> LiquidationMultiplierTypeKind:
    if obj["kind"] == "Discount":
        return Discount()
    if obj["kind"] == "Premium":
        return Premium()
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen("Discount" / borsh.CStruct(), "Premium" / borsh.CStruct())
