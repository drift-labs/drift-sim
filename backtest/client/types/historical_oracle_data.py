from __future__ import annotations
import typing
from dataclasses import dataclass
from construct import Container
import borsh_construct as borsh


class HistoricalOracleDataJSON(typing.TypedDict):
    last_oracle_price: int
    last_oracle_conf: int
    last_oracle_delay: int
    last_oracle_price_twap: int
    last_oracle_price_twap5min: int
    last_oracle_price_twap_ts: int


@dataclass
class HistoricalOracleData:
    layout: typing.ClassVar = borsh.CStruct(
        "last_oracle_price" / borsh.I128,
        "last_oracle_conf" / borsh.U128,
        "last_oracle_delay" / borsh.I64,
        "last_oracle_price_twap" / borsh.I128,
        "last_oracle_price_twap5min" / borsh.I128,
        "last_oracle_price_twap_ts" / borsh.I64,
    )
    last_oracle_price: int
    last_oracle_conf: int
    last_oracle_delay: int
    last_oracle_price_twap: int
    last_oracle_price_twap5min: int
    last_oracle_price_twap_ts: int

    @classmethod
    def from_decoded(cls, obj: Container) -> "HistoricalOracleData":
        return cls(
            last_oracle_price=obj.last_oracle_price,
            last_oracle_conf=obj.last_oracle_conf,
            last_oracle_delay=obj.last_oracle_delay,
            last_oracle_price_twap=obj.last_oracle_price_twap,
            last_oracle_price_twap5min=obj.last_oracle_price_twap5min,
            last_oracle_price_twap_ts=obj.last_oracle_price_twap_ts,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "last_oracle_price": self.last_oracle_price,
            "last_oracle_conf": self.last_oracle_conf,
            "last_oracle_delay": self.last_oracle_delay,
            "last_oracle_price_twap": self.last_oracle_price_twap,
            "last_oracle_price_twap5min": self.last_oracle_price_twap5min,
            "last_oracle_price_twap_ts": self.last_oracle_price_twap_ts,
        }

    def to_json(self) -> HistoricalOracleDataJSON:
        return {
            "last_oracle_price": self.last_oracle_price,
            "last_oracle_conf": self.last_oracle_conf,
            "last_oracle_delay": self.last_oracle_delay,
            "last_oracle_price_twap": self.last_oracle_price_twap,
            "last_oracle_price_twap5min": self.last_oracle_price_twap5min,
            "last_oracle_price_twap_ts": self.last_oracle_price_twap_ts,
        }

    @classmethod
    def from_json(cls, obj: HistoricalOracleDataJSON) -> "HistoricalOracleData":
        return cls(
            last_oracle_price=obj["last_oracle_price"],
            last_oracle_conf=obj["last_oracle_conf"],
            last_oracle_delay=obj["last_oracle_delay"],
            last_oracle_price_twap=obj["last_oracle_price_twap"],
            last_oracle_price_twap5min=obj["last_oracle_price_twap5min"],
            last_oracle_price_twap_ts=obj["last_oracle_price_twap_ts"],
        )
