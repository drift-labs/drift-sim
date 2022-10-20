from __future__ import annotations
import typing
from dataclasses import dataclass
from construct import Container
import borsh_construct as borsh


class ValidityGuardRailsJSON(typing.TypedDict):
    slots_before_stale_for_amm: int
    slots_before_stale_for_margin: int
    confidence_interval_max_size: int
    too_volatile_ratio: int


@dataclass
class ValidityGuardRails:
    layout: typing.ClassVar = borsh.CStruct(
        "slots_before_stale_for_amm" / borsh.I64,
        "slots_before_stale_for_margin" / borsh.I64,
        "confidence_interval_max_size" / borsh.U128,
        "too_volatile_ratio" / borsh.I128,
    )
    slots_before_stale_for_amm: int
    slots_before_stale_for_margin: int
    confidence_interval_max_size: int
    too_volatile_ratio: int

    @classmethod
    def from_decoded(cls, obj: Container) -> "ValidityGuardRails":
        return cls(
            slots_before_stale_for_amm=obj.slots_before_stale_for_amm,
            slots_before_stale_for_margin=obj.slots_before_stale_for_margin,
            confidence_interval_max_size=obj.confidence_interval_max_size,
            too_volatile_ratio=obj.too_volatile_ratio,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "slots_before_stale_for_amm": self.slots_before_stale_for_amm,
            "slots_before_stale_for_margin": self.slots_before_stale_for_margin,
            "confidence_interval_max_size": self.confidence_interval_max_size,
            "too_volatile_ratio": self.too_volatile_ratio,
        }

    def to_json(self) -> ValidityGuardRailsJSON:
        return {
            "slots_before_stale_for_amm": self.slots_before_stale_for_amm,
            "slots_before_stale_for_margin": self.slots_before_stale_for_margin,
            "confidence_interval_max_size": self.confidence_interval_max_size,
            "too_volatile_ratio": self.too_volatile_ratio,
        }

    @classmethod
    def from_json(cls, obj: ValidityGuardRailsJSON) -> "ValidityGuardRails":
        return cls(
            slots_before_stale_for_amm=obj["slots_before_stale_for_amm"],
            slots_before_stale_for_margin=obj["slots_before_stale_for_margin"],
            confidence_interval_max_size=obj["confidence_interval_max_size"],
            too_volatile_ratio=obj["too_volatile_ratio"],
        )
