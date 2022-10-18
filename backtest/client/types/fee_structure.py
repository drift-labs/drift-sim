from __future__ import annotations
from . import (
    fee_tier,
    order_filler_reward_structure,
)
import typing
from dataclasses import dataclass
from construct import Container
import borsh_construct as borsh


class FeeStructureJSON(typing.TypedDict):
    fee_tiers: list[fee_tier.FeeTierJSON]
    filler_reward_structure: order_filler_reward_structure.OrderFillerRewardStructureJSON
    referrer_reward_epoch_upper_bound: int
    flat_filler_fee: int


@dataclass
class FeeStructure:
    layout: typing.ClassVar = borsh.CStruct(
        "fee_tiers" / fee_tier.FeeTier.layout[10],
        "filler_reward_structure"
        / order_filler_reward_structure.OrderFillerRewardStructure.layout,
        "referrer_reward_epoch_upper_bound" / borsh.U64,
        "flat_filler_fee" / borsh.U64,
    )
    fee_tiers: list[fee_tier.FeeTier]
    filler_reward_structure: order_filler_reward_structure.OrderFillerRewardStructure
    referrer_reward_epoch_upper_bound: int
    flat_filler_fee: int

    @classmethod
    def from_decoded(cls, obj: Container) -> "FeeStructure":
        return cls(
            fee_tiers=list(
                map(lambda item: fee_tier.FeeTier.from_decoded(item), obj.fee_tiers)
            ),
            filler_reward_structure=order_filler_reward_structure.OrderFillerRewardStructure.from_decoded(
                obj.filler_reward_structure
            ),
            referrer_reward_epoch_upper_bound=obj.referrer_reward_epoch_upper_bound,
            flat_filler_fee=obj.flat_filler_fee,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "fee_tiers": list(map(lambda item: item.to_encodable(), self.fee_tiers)),
            "filler_reward_structure": self.filler_reward_structure.to_encodable(),
            "referrer_reward_epoch_upper_bound": self.referrer_reward_epoch_upper_bound,
            "flat_filler_fee": self.flat_filler_fee,
        }

    def to_json(self) -> FeeStructureJSON:
        return {
            "fee_tiers": list(map(lambda item: item.to_json(), self.fee_tiers)),
            "filler_reward_structure": self.filler_reward_structure.to_json(),
            "referrer_reward_epoch_upper_bound": self.referrer_reward_epoch_upper_bound,
            "flat_filler_fee": self.flat_filler_fee,
        }

    @classmethod
    def from_json(cls, obj: FeeStructureJSON) -> "FeeStructure":
        return cls(
            fee_tiers=list(
                map(lambda item: fee_tier.FeeTier.from_json(item), obj["fee_tiers"])
            ),
            filler_reward_structure=order_filler_reward_structure.OrderFillerRewardStructure.from_json(
                obj["filler_reward_structure"]
            ),
            referrer_reward_epoch_upper_bound=obj["referrer_reward_epoch_upper_bound"],
            flat_filler_fee=obj["flat_filler_fee"],
        )
