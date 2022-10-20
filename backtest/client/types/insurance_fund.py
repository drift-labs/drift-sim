from __future__ import annotations
import typing
from dataclasses import dataclass
from construct import Container
from solana.publickey import PublicKey
from anchorpy.borsh_extension import BorshPubkey
import borsh_construct as borsh


class InsuranceFundJSON(typing.TypedDict):
    vault: str
    total_shares: int
    user_shares: int
    shares_base: int
    unstaking_period: int
    last_revenue_settle_ts: int
    revenue_settle_period: int
    total_factor: int
    user_factor: int


@dataclass
class InsuranceFund:
    layout: typing.ClassVar = borsh.CStruct(
        "vault" / BorshPubkey,
        "total_shares" / borsh.U128,
        "user_shares" / borsh.U128,
        "shares_base" / borsh.U128,
        "unstaking_period" / borsh.I64,
        "last_revenue_settle_ts" / borsh.I64,
        "revenue_settle_period" / borsh.I64,
        "total_factor" / borsh.U32,
        "user_factor" / borsh.U32,
    )
    vault: PublicKey
    total_shares: int
    user_shares: int
    shares_base: int
    unstaking_period: int
    last_revenue_settle_ts: int
    revenue_settle_period: int
    total_factor: int
    user_factor: int

    @classmethod
    def from_decoded(cls, obj: Container) -> "InsuranceFund":
        return cls(
            vault=obj.vault,
            total_shares=obj.total_shares,
            user_shares=obj.user_shares,
            shares_base=obj.shares_base,
            unstaking_period=obj.unstaking_period,
            last_revenue_settle_ts=obj.last_revenue_settle_ts,
            revenue_settle_period=obj.revenue_settle_period,
            total_factor=obj.total_factor,
            user_factor=obj.user_factor,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "vault": self.vault,
            "total_shares": self.total_shares,
            "user_shares": self.user_shares,
            "shares_base": self.shares_base,
            "unstaking_period": self.unstaking_period,
            "last_revenue_settle_ts": self.last_revenue_settle_ts,
            "revenue_settle_period": self.revenue_settle_period,
            "total_factor": self.total_factor,
            "user_factor": self.user_factor,
        }

    def to_json(self) -> InsuranceFundJSON:
        return {
            "vault": str(self.vault),
            "total_shares": self.total_shares,
            "user_shares": self.user_shares,
            "shares_base": self.shares_base,
            "unstaking_period": self.unstaking_period,
            "last_revenue_settle_ts": self.last_revenue_settle_ts,
            "revenue_settle_period": self.revenue_settle_period,
            "total_factor": self.total_factor,
            "user_factor": self.user_factor,
        }

    @classmethod
    def from_json(cls, obj: InsuranceFundJSON) -> "InsuranceFund":
        return cls(
            vault=PublicKey(obj["vault"]),
            total_shares=obj["total_shares"],
            user_shares=obj["user_shares"],
            shares_base=obj["shares_base"],
            unstaking_period=obj["unstaking_period"],
            last_revenue_settle_ts=obj["last_revenue_settle_ts"],
            revenue_settle_period=obj["revenue_settle_period"],
            total_factor=obj["total_factor"],
            user_factor=obj["user_factor"],
        )
