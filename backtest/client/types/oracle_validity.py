from __future__ import annotations
import typing
from dataclasses import dataclass
from anchorpy.borsh_extension import EnumForCodegen
import borsh_construct as borsh


class InvalidJSON(typing.TypedDict):
    kind: typing.Literal["Invalid"]


class TooVolatileJSON(typing.TypedDict):
    kind: typing.Literal["TooVolatile"]


class StaleForMarginJSON(typing.TypedDict):
    kind: typing.Literal["StaleForMargin"]


class InsufficientDataPointsJSON(typing.TypedDict):
    kind: typing.Literal["InsufficientDataPoints"]


class StaleForAMMJSON(typing.TypedDict):
    kind: typing.Literal["StaleForAMM"]


class ValidJSON(typing.TypedDict):
    kind: typing.Literal["Valid"]


@dataclass
class Invalid:
    discriminator: typing.ClassVar = 0
    kind: typing.ClassVar = "Invalid"

    @classmethod
    def to_json(cls) -> InvalidJSON:
        return InvalidJSON(
            kind="Invalid",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Invalid": {},
        }


@dataclass
class TooVolatile:
    discriminator: typing.ClassVar = 1
    kind: typing.ClassVar = "TooVolatile"

    @classmethod
    def to_json(cls) -> TooVolatileJSON:
        return TooVolatileJSON(
            kind="TooVolatile",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "TooVolatile": {},
        }


@dataclass
class StaleForMargin:
    discriminator: typing.ClassVar = 2
    kind: typing.ClassVar = "StaleForMargin"

    @classmethod
    def to_json(cls) -> StaleForMarginJSON:
        return StaleForMarginJSON(
            kind="StaleForMargin",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "StaleForMargin": {},
        }


@dataclass
class InsufficientDataPoints:
    discriminator: typing.ClassVar = 3
    kind: typing.ClassVar = "InsufficientDataPoints"

    @classmethod
    def to_json(cls) -> InsufficientDataPointsJSON:
        return InsufficientDataPointsJSON(
            kind="InsufficientDataPoints",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "InsufficientDataPoints": {},
        }


@dataclass
class StaleForAMM:
    discriminator: typing.ClassVar = 4
    kind: typing.ClassVar = "StaleForAMM"

    @classmethod
    def to_json(cls) -> StaleForAMMJSON:
        return StaleForAMMJSON(
            kind="StaleForAMM",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "StaleForAMM": {},
        }


@dataclass
class Valid:
    discriminator: typing.ClassVar = 5
    kind: typing.ClassVar = "Valid"

    @classmethod
    def to_json(cls) -> ValidJSON:
        return ValidJSON(
            kind="Valid",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Valid": {},
        }


OracleValidityKind = typing.Union[
    Invalid, TooVolatile, StaleForMargin, InsufficientDataPoints, StaleForAMM, Valid
]
OracleValidityJSON = typing.Union[
    InvalidJSON,
    TooVolatileJSON,
    StaleForMarginJSON,
    InsufficientDataPointsJSON,
    StaleForAMMJSON,
    ValidJSON,
]


def from_decoded(obj: dict) -> OracleValidityKind:
    if not isinstance(obj, dict):
        raise ValueError("Invalid enum object")
    if "Invalid" in obj:
        return Invalid()
    if "TooVolatile" in obj:
        return TooVolatile()
    if "StaleForMargin" in obj:
        return StaleForMargin()
    if "InsufficientDataPoints" in obj:
        return InsufficientDataPoints()
    if "StaleForAMM" in obj:
        return StaleForAMM()
    if "Valid" in obj:
        return Valid()
    raise ValueError("Invalid enum object")


def from_json(obj: OracleValidityJSON) -> OracleValidityKind:
    if obj["kind"] == "Invalid":
        return Invalid()
    if obj["kind"] == "TooVolatile":
        return TooVolatile()
    if obj["kind"] == "StaleForMargin":
        return StaleForMargin()
    if obj["kind"] == "InsufficientDataPoints":
        return InsufficientDataPoints()
    if obj["kind"] == "StaleForAMM":
        return StaleForAMM()
    if obj["kind"] == "Valid":
        return Valid()
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen(
    "Invalid" / borsh.CStruct(),
    "TooVolatile" / borsh.CStruct(),
    "StaleForMargin" / borsh.CStruct(),
    "InsufficientDataPoints" / borsh.CStruct(),
    "StaleForAMM" / borsh.CStruct(),
    "Valid" / borsh.CStruct(),
)
