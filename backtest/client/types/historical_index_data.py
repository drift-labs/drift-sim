from __future__ import annotations
import typing
from dataclasses import dataclass
from construct import Container
import borsh_construct as borsh


class HistoricalIndexDataJSON(typing.TypedDict):
    last_index_bid_price: int
    last_index_ask_price: int
    last_index_price_twap: int
    last_index_price_twap5min: int
    last_index_price_twap_ts: int


@dataclass
class HistoricalIndexData:
    layout: typing.ClassVar = borsh.CStruct(
        "last_index_bid_price" / borsh.U128,
        "last_index_ask_price" / borsh.U128,
        "last_index_price_twap" / borsh.U128,
        "last_index_price_twap5min" / borsh.U128,
        "last_index_price_twap_ts" / borsh.I64,
    )
    last_index_bid_price: int
    last_index_ask_price: int
    last_index_price_twap: int
    last_index_price_twap5min: int
    last_index_price_twap_ts: int

    @classmethod
    def from_decoded(cls, obj: Container) -> "HistoricalIndexData":
        return cls(
            last_index_bid_price=obj.last_index_bid_price,
            last_index_ask_price=obj.last_index_ask_price,
            last_index_price_twap=obj.last_index_price_twap,
            last_index_price_twap5min=obj.last_index_price_twap5min,
            last_index_price_twap_ts=obj.last_index_price_twap_ts,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "last_index_bid_price": self.last_index_bid_price,
            "last_index_ask_price": self.last_index_ask_price,
            "last_index_price_twap": self.last_index_price_twap,
            "last_index_price_twap5min": self.last_index_price_twap5min,
            "last_index_price_twap_ts": self.last_index_price_twap_ts,
        }

    def to_json(self) -> HistoricalIndexDataJSON:
        return {
            "last_index_bid_price": self.last_index_bid_price,
            "last_index_ask_price": self.last_index_ask_price,
            "last_index_price_twap": self.last_index_price_twap,
            "last_index_price_twap5min": self.last_index_price_twap5min,
            "last_index_price_twap_ts": self.last_index_price_twap_ts,
        }

    @classmethod
    def from_json(cls, obj: HistoricalIndexDataJSON) -> "HistoricalIndexData":
        return cls(
            last_index_bid_price=obj["last_index_bid_price"],
            last_index_ask_price=obj["last_index_ask_price"],
            last_index_price_twap=obj["last_index_price_twap"],
            last_index_price_twap5min=obj["last_index_price_twap5min"],
            last_index_price_twap_ts=obj["last_index_price_twap_ts"],
        )
