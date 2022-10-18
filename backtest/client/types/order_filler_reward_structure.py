from __future__ import annotations
import typing
from dataclasses import dataclass
from construct import Container
import borsh_construct as borsh


class OrderFillerRewardStructureJSON(typing.TypedDict):
    reward_numerator: int
    reward_denominator: int
    time_based_reward_lower_bound: int


@dataclass
class OrderFillerRewardStructure:
    layout: typing.ClassVar = borsh.CStruct(
        "reward_numerator" / borsh.U32,
        "reward_denominator" / borsh.U32,
        "time_based_reward_lower_bound" / borsh.U128,
    )
    reward_numerator: int
    reward_denominator: int
    time_based_reward_lower_bound: int

    @classmethod
    def from_decoded(cls, obj: Container) -> "OrderFillerRewardStructure":
        return cls(
            reward_numerator=obj.reward_numerator,
            reward_denominator=obj.reward_denominator,
            time_based_reward_lower_bound=obj.time_based_reward_lower_bound,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "reward_numerator": self.reward_numerator,
            "reward_denominator": self.reward_denominator,
            "time_based_reward_lower_bound": self.time_based_reward_lower_bound,
        }

    def to_json(self) -> OrderFillerRewardStructureJSON:
        return {
            "reward_numerator": self.reward_numerator,
            "reward_denominator": self.reward_denominator,
            "time_based_reward_lower_bound": self.time_based_reward_lower_bound,
        }

    @classmethod
    def from_json(
        cls, obj: OrderFillerRewardStructureJSON
    ) -> "OrderFillerRewardStructure":
        return cls(
            reward_numerator=obj["reward_numerator"],
            reward_denominator=obj["reward_denominator"],
            time_based_reward_lower_bound=obj["time_based_reward_lower_bound"],
        )
