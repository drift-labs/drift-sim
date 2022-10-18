from __future__ import annotations
import typing
from dataclasses import dataclass
from construct import Container
import borsh_construct as borsh


class InsuranceClaimJSON(typing.TypedDict):
    revenue_withdraw_since_last_settle: int
    max_revenue_withdraw_per_period: int
    quote_max_insurance: int
    quote_settled_insurance: int
    last_revenue_withdraw_ts: int


@dataclass
class InsuranceClaim:
    layout: typing.ClassVar = borsh.CStruct(
        "revenue_withdraw_since_last_settle" / borsh.U128,
        "max_revenue_withdraw_per_period" / borsh.U128,
        "quote_max_insurance" / borsh.U128,
        "quote_settled_insurance" / borsh.U128,
        "last_revenue_withdraw_ts" / borsh.I64,
    )
    revenue_withdraw_since_last_settle: int
    max_revenue_withdraw_per_period: int
    quote_max_insurance: int
    quote_settled_insurance: int
    last_revenue_withdraw_ts: int

    @classmethod
    def from_decoded(cls, obj: Container) -> "InsuranceClaim":
        return cls(
            revenue_withdraw_since_last_settle=obj.revenue_withdraw_since_last_settle,
            max_revenue_withdraw_per_period=obj.max_revenue_withdraw_per_period,
            quote_max_insurance=obj.quote_max_insurance,
            quote_settled_insurance=obj.quote_settled_insurance,
            last_revenue_withdraw_ts=obj.last_revenue_withdraw_ts,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "revenue_withdraw_since_last_settle": self.revenue_withdraw_since_last_settle,
            "max_revenue_withdraw_per_period": self.max_revenue_withdraw_per_period,
            "quote_max_insurance": self.quote_max_insurance,
            "quote_settled_insurance": self.quote_settled_insurance,
            "last_revenue_withdraw_ts": self.last_revenue_withdraw_ts,
        }

    def to_json(self) -> InsuranceClaimJSON:
        return {
            "revenue_withdraw_since_last_settle": self.revenue_withdraw_since_last_settle,
            "max_revenue_withdraw_per_period": self.max_revenue_withdraw_per_period,
            "quote_max_insurance": self.quote_max_insurance,
            "quote_settled_insurance": self.quote_settled_insurance,
            "last_revenue_withdraw_ts": self.last_revenue_withdraw_ts,
        }

    @classmethod
    def from_json(cls, obj: InsuranceClaimJSON) -> "InsuranceClaim":
        return cls(
            revenue_withdraw_since_last_settle=obj[
                "revenue_withdraw_since_last_settle"
            ],
            max_revenue_withdraw_per_period=obj["max_revenue_withdraw_per_period"],
            quote_max_insurance=obj["quote_max_insurance"],
            quote_settled_insurance=obj["quote_settled_insurance"],
            last_revenue_withdraw_ts=obj["last_revenue_withdraw_ts"],
        )
