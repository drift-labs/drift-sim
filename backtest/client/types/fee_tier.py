from __future__ import annotations
import typing
from dataclasses import dataclass
from construct import Container
import borsh_construct as borsh


class FeeTierJSON(typing.TypedDict):
    fee_numerator: int
    fee_denominator: int
    maker_rebate_numerator: int
    maker_rebate_denominator: int
    referrer_reward_numerator: int
    referrer_reward_denominator: int
    referee_fee_numerator: int
    referee_fee_denominator: int


@dataclass
class FeeTier:
    layout: typing.ClassVar = borsh.CStruct(
        "fee_numerator" / borsh.U32,
        "fee_denominator" / borsh.U32,
        "maker_rebate_numerator" / borsh.U32,
        "maker_rebate_denominator" / borsh.U32,
        "referrer_reward_numerator" / borsh.U32,
        "referrer_reward_denominator" / borsh.U32,
        "referee_fee_numerator" / borsh.U32,
        "referee_fee_denominator" / borsh.U32,
    )
    fee_numerator: int
    fee_denominator: int
    maker_rebate_numerator: int
    maker_rebate_denominator: int
    referrer_reward_numerator: int
    referrer_reward_denominator: int
    referee_fee_numerator: int
    referee_fee_denominator: int

    @classmethod
    def from_decoded(cls, obj: Container) -> "FeeTier":
        return cls(
            fee_numerator=obj.fee_numerator,
            fee_denominator=obj.fee_denominator,
            maker_rebate_numerator=obj.maker_rebate_numerator,
            maker_rebate_denominator=obj.maker_rebate_denominator,
            referrer_reward_numerator=obj.referrer_reward_numerator,
            referrer_reward_denominator=obj.referrer_reward_denominator,
            referee_fee_numerator=obj.referee_fee_numerator,
            referee_fee_denominator=obj.referee_fee_denominator,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "fee_numerator": self.fee_numerator,
            "fee_denominator": self.fee_denominator,
            "maker_rebate_numerator": self.maker_rebate_numerator,
            "maker_rebate_denominator": self.maker_rebate_denominator,
            "referrer_reward_numerator": self.referrer_reward_numerator,
            "referrer_reward_denominator": self.referrer_reward_denominator,
            "referee_fee_numerator": self.referee_fee_numerator,
            "referee_fee_denominator": self.referee_fee_denominator,
        }

    def to_json(self) -> FeeTierJSON:
        return {
            "fee_numerator": self.fee_numerator,
            "fee_denominator": self.fee_denominator,
            "maker_rebate_numerator": self.maker_rebate_numerator,
            "maker_rebate_denominator": self.maker_rebate_denominator,
            "referrer_reward_numerator": self.referrer_reward_numerator,
            "referrer_reward_denominator": self.referrer_reward_denominator,
            "referee_fee_numerator": self.referee_fee_numerator,
            "referee_fee_denominator": self.referee_fee_denominator,
        }

    @classmethod
    def from_json(cls, obj: FeeTierJSON) -> "FeeTier":
        return cls(
            fee_numerator=obj["fee_numerator"],
            fee_denominator=obj["fee_denominator"],
            maker_rebate_numerator=obj["maker_rebate_numerator"],
            maker_rebate_denominator=obj["maker_rebate_denominator"],
            referrer_reward_numerator=obj["referrer_reward_numerator"],
            referrer_reward_denominator=obj["referrer_reward_denominator"],
            referee_fee_numerator=obj["referee_fee_numerator"],
            referee_fee_denominator=obj["referee_fee_denominator"],
        )
