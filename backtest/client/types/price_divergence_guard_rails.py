from __future__ import annotations
import typing
from dataclasses import dataclass
from construct import Container
import borsh_construct as borsh


class PriceDivergenceGuardRailsJSON(typing.TypedDict):
    mark_oracle_divergence_numerator: int
    mark_oracle_divergence_denominator: int


@dataclass
class PriceDivergenceGuardRails:
    layout: typing.ClassVar = borsh.CStruct(
        "mark_oracle_divergence_numerator" / borsh.U128,
        "mark_oracle_divergence_denominator" / borsh.U128,
    )
    mark_oracle_divergence_numerator: int
    mark_oracle_divergence_denominator: int

    @classmethod
    def from_decoded(cls, obj: Container) -> "PriceDivergenceGuardRails":
        return cls(
            mark_oracle_divergence_numerator=obj.mark_oracle_divergence_numerator,
            mark_oracle_divergence_denominator=obj.mark_oracle_divergence_denominator,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "mark_oracle_divergence_numerator": self.mark_oracle_divergence_numerator,
            "mark_oracle_divergence_denominator": self.mark_oracle_divergence_denominator,
        }

    def to_json(self) -> PriceDivergenceGuardRailsJSON:
        return {
            "mark_oracle_divergence_numerator": self.mark_oracle_divergence_numerator,
            "mark_oracle_divergence_denominator": self.mark_oracle_divergence_denominator,
        }

    @classmethod
    def from_json(
        cls, obj: PriceDivergenceGuardRailsJSON
    ) -> "PriceDivergenceGuardRails":
        return cls(
            mark_oracle_divergence_numerator=obj["mark_oracle_divergence_numerator"],
            mark_oracle_divergence_denominator=obj[
                "mark_oracle_divergence_denominator"
            ],
        )
