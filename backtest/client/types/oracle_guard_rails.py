from __future__ import annotations
from . import (
    price_divergence_guard_rails,
    validity_guard_rails,
)
import typing
from dataclasses import dataclass
from construct import Container
import borsh_construct as borsh


class OracleGuardRailsJSON(typing.TypedDict):
    price_divergence: price_divergence_guard_rails.PriceDivergenceGuardRailsJSON
    validity: validity_guard_rails.ValidityGuardRailsJSON
    use_for_liquidations: bool


@dataclass
class OracleGuardRails:
    layout: typing.ClassVar = borsh.CStruct(
        "price_divergence"
        / price_divergence_guard_rails.PriceDivergenceGuardRails.layout,
        "validity" / validity_guard_rails.ValidityGuardRails.layout,
        "use_for_liquidations" / borsh.Bool,
    )
    price_divergence: price_divergence_guard_rails.PriceDivergenceGuardRails
    validity: validity_guard_rails.ValidityGuardRails
    use_for_liquidations: bool

    @classmethod
    def from_decoded(cls, obj: Container) -> "OracleGuardRails":
        return cls(
            price_divergence=price_divergence_guard_rails.PriceDivergenceGuardRails.from_decoded(
                obj.price_divergence
            ),
            validity=validity_guard_rails.ValidityGuardRails.from_decoded(obj.validity),
            use_for_liquidations=obj.use_for_liquidations,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "price_divergence": self.price_divergence.to_encodable(),
            "validity": self.validity.to_encodable(),
            "use_for_liquidations": self.use_for_liquidations,
        }

    def to_json(self) -> OracleGuardRailsJSON:
        return {
            "price_divergence": self.price_divergence.to_json(),
            "validity": self.validity.to_json(),
            "use_for_liquidations": self.use_for_liquidations,
        }

    @classmethod
    def from_json(cls, obj: OracleGuardRailsJSON) -> "OracleGuardRails":
        return cls(
            price_divergence=price_divergence_guard_rails.PriceDivergenceGuardRails.from_json(
                obj["price_divergence"]
            ),
            validity=validity_guard_rails.ValidityGuardRails.from_json(obj["validity"]),
            use_for_liquidations=obj["use_for_liquidations"],
        )
