from __future__ import annotations
import typing
from dataclasses import dataclass
from anchorpy.borsh_extension import EnumForCodegen
import borsh_construct as borsh

AMMJSONValue = tuple[typing.Optional[int]]
AMMValue = tuple[typing.Optional[int]]


class AMMJSON(typing.TypedDict):
    value: AMMJSONValue
    kind: typing.Literal["AMM"]


class MatchJSON(typing.TypedDict):
    kind: typing.Literal["Match"]


@dataclass
class AMM:
    discriminator: typing.ClassVar = 0
    kind: typing.ClassVar = "AMM"
    value: AMMValue

    def to_json(self) -> AMMJSON:
        return AMMJSON(
            kind="AMM",
            value=(self.value[0],),
        )

    def to_encodable(self) -> dict:
        return {
            "AMM": {
                "item_0": self.value[0],
            },
        }


@dataclass
class Match:
    discriminator: typing.ClassVar = 1
    kind: typing.ClassVar = "Match"

    @classmethod
    def to_json(cls) -> MatchJSON:
        return MatchJSON(
            kind="Match",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Match": {},
        }


PerpFulfillmentMethodKind = typing.Union[AMM, Match]
PerpFulfillmentMethodJSON = typing.Union[AMMJSON, MatchJSON]


def from_decoded(obj: dict) -> PerpFulfillmentMethodKind:
    if not isinstance(obj, dict):
        raise ValueError("Invalid enum object")
    if "AMM" in obj:
        val = obj["AMM"]
        return AMM((val["item_0"],))
    if "Match" in obj:
        return Match()
    raise ValueError("Invalid enum object")


def from_json(obj: PerpFulfillmentMethodJSON) -> PerpFulfillmentMethodKind:
    if obj["kind"] == "AMM":
        ammjson_value = typing.cast(AMMJSONValue, obj["value"])
        return AMM((ammjson_value[0],))
    if obj["kind"] == "Match":
        return Match()
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen(
    "AMM" / borsh.CStruct("item_0" / borsh.Option(borsh.U128)),
    "Match" / borsh.CStruct(),
)
