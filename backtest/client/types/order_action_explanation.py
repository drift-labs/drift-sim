from __future__ import annotations
import typing
from dataclasses import dataclass
from anchorpy.borsh_extension import EnumForCodegen
import borsh_construct as borsh


class NoneJSON(typing.TypedDict):
    kind: typing.Literal["None"]


class InsufficientFreeCollateralJSON(typing.TypedDict):
    kind: typing.Literal["InsufficientFreeCollateral"]


class OraclePriceBreachedLimitPriceJSON(typing.TypedDict):
    kind: typing.Literal["OraclePriceBreachedLimitPrice"]


class MarketOrderFilledToLimitPriceJSON(typing.TypedDict):
    kind: typing.Literal["MarketOrderFilledToLimitPrice"]


class OrderExpiredJSON(typing.TypedDict):
    kind: typing.Literal["OrderExpired"]


class CanceledForLiquidationJSON(typing.TypedDict):
    kind: typing.Literal["CanceledForLiquidation"]


class OrderFilledWithAMMJSON(typing.TypedDict):
    kind: typing.Literal["OrderFilledWithAMM"]


class OrderFilledWithMatchJSON(typing.TypedDict):
    kind: typing.Literal["OrderFilledWithMatch"]


class MarketExpiredJSON(typing.TypedDict):
    kind: typing.Literal["MarketExpired"]


@dataclass
class None_:
    discriminator: typing.ClassVar = 0
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


@dataclass
class InsufficientFreeCollateral:
    discriminator: typing.ClassVar = 1
    kind: typing.ClassVar = "InsufficientFreeCollateral"

    @classmethod
    def to_json(cls) -> InsufficientFreeCollateralJSON:
        return InsufficientFreeCollateralJSON(
            kind="InsufficientFreeCollateral",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "InsufficientFreeCollateral": {},
        }


@dataclass
class OraclePriceBreachedLimitPrice:
    discriminator: typing.ClassVar = 2
    kind: typing.ClassVar = "OraclePriceBreachedLimitPrice"

    @classmethod
    def to_json(cls) -> OraclePriceBreachedLimitPriceJSON:
        return OraclePriceBreachedLimitPriceJSON(
            kind="OraclePriceBreachedLimitPrice",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "OraclePriceBreachedLimitPrice": {},
        }


@dataclass
class MarketOrderFilledToLimitPrice:
    discriminator: typing.ClassVar = 3
    kind: typing.ClassVar = "MarketOrderFilledToLimitPrice"

    @classmethod
    def to_json(cls) -> MarketOrderFilledToLimitPriceJSON:
        return MarketOrderFilledToLimitPriceJSON(
            kind="MarketOrderFilledToLimitPrice",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "MarketOrderFilledToLimitPrice": {},
        }


@dataclass
class OrderExpired:
    discriminator: typing.ClassVar = 4
    kind: typing.ClassVar = "OrderExpired"

    @classmethod
    def to_json(cls) -> OrderExpiredJSON:
        return OrderExpiredJSON(
            kind="OrderExpired",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "OrderExpired": {},
        }


@dataclass
class CanceledForLiquidation:
    discriminator: typing.ClassVar = 5
    kind: typing.ClassVar = "CanceledForLiquidation"

    @classmethod
    def to_json(cls) -> CanceledForLiquidationJSON:
        return CanceledForLiquidationJSON(
            kind="CanceledForLiquidation",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "CanceledForLiquidation": {},
        }


@dataclass
class OrderFilledWithAMM:
    discriminator: typing.ClassVar = 6
    kind: typing.ClassVar = "OrderFilledWithAMM"

    @classmethod
    def to_json(cls) -> OrderFilledWithAMMJSON:
        return OrderFilledWithAMMJSON(
            kind="OrderFilledWithAMM",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "OrderFilledWithAMM": {},
        }


@dataclass
class OrderFilledWithMatch:
    discriminator: typing.ClassVar = 7
    kind: typing.ClassVar = "OrderFilledWithMatch"

    @classmethod
    def to_json(cls) -> OrderFilledWithMatchJSON:
        return OrderFilledWithMatchJSON(
            kind="OrderFilledWithMatch",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "OrderFilledWithMatch": {},
        }


@dataclass
class MarketExpired:
    discriminator: typing.ClassVar = 8
    kind: typing.ClassVar = "MarketExpired"

    @classmethod
    def to_json(cls) -> MarketExpiredJSON:
        return MarketExpiredJSON(
            kind="MarketExpired",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "MarketExpired": {},
        }


OrderActionExplanationKind = typing.Union[
    None_,
    InsufficientFreeCollateral,
    OraclePriceBreachedLimitPrice,
    MarketOrderFilledToLimitPrice,
    OrderExpired,
    CanceledForLiquidation,
    OrderFilledWithAMM,
    OrderFilledWithMatch,
    MarketExpired,
]
OrderActionExplanationJSON = typing.Union[
    NoneJSON,
    InsufficientFreeCollateralJSON,
    OraclePriceBreachedLimitPriceJSON,
    MarketOrderFilledToLimitPriceJSON,
    OrderExpiredJSON,
    CanceledForLiquidationJSON,
    OrderFilledWithAMMJSON,
    OrderFilledWithMatchJSON,
    MarketExpiredJSON,
]


def from_decoded(obj: dict) -> OrderActionExplanationKind:
    if not isinstance(obj, dict):
        raise ValueError("Invalid enum object")
    if "None" in obj:
        return None_()
    if "InsufficientFreeCollateral" in obj:
        return InsufficientFreeCollateral()
    if "OraclePriceBreachedLimitPrice" in obj:
        return OraclePriceBreachedLimitPrice()
    if "MarketOrderFilledToLimitPrice" in obj:
        return MarketOrderFilledToLimitPrice()
    if "OrderExpired" in obj:
        return OrderExpired()
    if "CanceledForLiquidation" in obj:
        return CanceledForLiquidation()
    if "OrderFilledWithAMM" in obj:
        return OrderFilledWithAMM()
    if "OrderFilledWithMatch" in obj:
        return OrderFilledWithMatch()
    if "MarketExpired" in obj:
        return MarketExpired()
    raise ValueError("Invalid enum object")


def from_json(obj: OrderActionExplanationJSON) -> OrderActionExplanationKind:
    if obj["kind"] == "None":
        return None_()
    if obj["kind"] == "InsufficientFreeCollateral":
        return InsufficientFreeCollateral()
    if obj["kind"] == "OraclePriceBreachedLimitPrice":
        return OraclePriceBreachedLimitPrice()
    if obj["kind"] == "MarketOrderFilledToLimitPrice":
        return MarketOrderFilledToLimitPrice()
    if obj["kind"] == "OrderExpired":
        return OrderExpired()
    if obj["kind"] == "CanceledForLiquidation":
        return CanceledForLiquidation()
    if obj["kind"] == "OrderFilledWithAMM":
        return OrderFilledWithAMM()
    if obj["kind"] == "OrderFilledWithMatch":
        return OrderFilledWithMatch()
    if obj["kind"] == "MarketExpired":
        return MarketExpired()
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen(
    "None" / borsh.CStruct(),
    "InsufficientFreeCollateral" / borsh.CStruct(),
    "OraclePriceBreachedLimitPrice" / borsh.CStruct(),
    "MarketOrderFilledToLimitPrice" / borsh.CStruct(),
    "OrderExpired" / borsh.CStruct(),
    "CanceledForLiquidation" / borsh.CStruct(),
    "OrderFilledWithAMM" / borsh.CStruct(),
    "OrderFilledWithMatch" / borsh.CStruct(),
    "MarketExpired" / borsh.CStruct(),
)
