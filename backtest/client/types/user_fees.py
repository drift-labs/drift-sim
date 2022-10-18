from __future__ import annotations
import typing
from dataclasses import dataclass
from construct import Container
import borsh_construct as borsh


class UserFeesJSON(typing.TypedDict):
    total_fee_paid: int
    total_fee_rebate: int
    total_token_discount: int
    total_referee_discount: int
    total_referrer_reward: int
    current_epoch_referrer_reward: int


@dataclass
class UserFees:
    layout: typing.ClassVar = borsh.CStruct(
        "total_fee_paid" / borsh.U64,
        "total_fee_rebate" / borsh.U64,
        "total_token_discount" / borsh.U64,
        "total_referee_discount" / borsh.U64,
        "total_referrer_reward" / borsh.U64,
        "current_epoch_referrer_reward" / borsh.U64,
    )
    total_fee_paid: int
    total_fee_rebate: int
    total_token_discount: int
    total_referee_discount: int
    total_referrer_reward: int
    current_epoch_referrer_reward: int

    @classmethod
    def from_decoded(cls, obj: Container) -> "UserFees":
        return cls(
            total_fee_paid=obj.total_fee_paid,
            total_fee_rebate=obj.total_fee_rebate,
            total_token_discount=obj.total_token_discount,
            total_referee_discount=obj.total_referee_discount,
            total_referrer_reward=obj.total_referrer_reward,
            current_epoch_referrer_reward=obj.current_epoch_referrer_reward,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "total_fee_paid": self.total_fee_paid,
            "total_fee_rebate": self.total_fee_rebate,
            "total_token_discount": self.total_token_discount,
            "total_referee_discount": self.total_referee_discount,
            "total_referrer_reward": self.total_referrer_reward,
            "current_epoch_referrer_reward": self.current_epoch_referrer_reward,
        }

    def to_json(self) -> UserFeesJSON:
        return {
            "total_fee_paid": self.total_fee_paid,
            "total_fee_rebate": self.total_fee_rebate,
            "total_token_discount": self.total_token_discount,
            "total_referee_discount": self.total_referee_discount,
            "total_referrer_reward": self.total_referrer_reward,
            "current_epoch_referrer_reward": self.current_epoch_referrer_reward,
        }

    @classmethod
    def from_json(cls, obj: UserFeesJSON) -> "UserFees":
        return cls(
            total_fee_paid=obj["total_fee_paid"],
            total_fee_rebate=obj["total_fee_rebate"],
            total_token_discount=obj["total_token_discount"],
            total_referee_discount=obj["total_referee_discount"],
            total_referrer_reward=obj["total_referrer_reward"],
            current_epoch_referrer_reward=obj["current_epoch_referrer_reward"],
        )
