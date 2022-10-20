from __future__ import annotations
from . import (
    position_direction,
    order_type,
    order_trigger_condition,
    market_type,
)
import typing
from dataclasses import dataclass
from construct import Container
import borsh_construct as borsh


class OrderParamsJSON(typing.TypedDict):
    order_type: order_type.OrderTypeJSON
    market_type: market_type.MarketTypeJSON
    direction: position_direction.PositionDirectionJSON
    user_order_id: int
    base_asset_amount: int
    price: int
    market_index: int
    reduce_only: bool
    post_only: bool
    immediate_or_cancel: bool
    trigger_price: typing.Optional[int]
    trigger_condition: order_trigger_condition.OrderTriggerConditionJSON
    oracle_price_offset: typing.Optional[int]
    auction_duration: typing.Optional[int]
    time_in_force: typing.Optional[int]
    auction_start_price: typing.Optional[int]


@dataclass
class OrderParams:
    layout: typing.ClassVar = borsh.CStruct(
        "order_type" / order_type.layout,
        "market_type" / market_type.layout,
        "direction" / position_direction.layout,
        "user_order_id" / borsh.U8,
        "base_asset_amount" / borsh.U64,
        "price" / borsh.U64,
        "market_index" / borsh.U16,
        "reduce_only" / borsh.Bool,
        "post_only" / borsh.Bool,
        "immediate_or_cancel" / borsh.Bool,
        "trigger_price" / borsh.Option(borsh.U64),
        "trigger_condition" / order_trigger_condition.layout,
        "oracle_price_offset" / borsh.Option(borsh.I32),
        "auction_duration" / borsh.Option(borsh.U8),
        "time_in_force" / borsh.Option(borsh.U8),
        "auction_start_price" / borsh.Option(borsh.U64),
    )
    order_type: order_type.OrderTypeKind
    market_type: market_type.MarketTypeKind
    direction: position_direction.PositionDirectionKind
    user_order_id: int
    base_asset_amount: int
    price: int
    market_index: int
    reduce_only: bool
    post_only: bool
    immediate_or_cancel: bool
    trigger_price: typing.Optional[int]
    trigger_condition: order_trigger_condition.OrderTriggerConditionKind
    oracle_price_offset: typing.Optional[int]
    auction_duration: typing.Optional[int]
    time_in_force: typing.Optional[int]
    auction_start_price: typing.Optional[int]

    @classmethod
    def from_decoded(cls, obj: Container) -> "OrderParams":
        return cls(
            order_type=order_type.from_decoded(obj.order_type),
            market_type=market_type.from_decoded(obj.market_type),
            direction=position_direction.from_decoded(obj.direction),
            user_order_id=obj.user_order_id,
            base_asset_amount=obj.base_asset_amount,
            price=obj.price,
            market_index=obj.market_index,
            reduce_only=obj.reduce_only,
            post_only=obj.post_only,
            immediate_or_cancel=obj.immediate_or_cancel,
            trigger_price=obj.trigger_price,
            trigger_condition=order_trigger_condition.from_decoded(
                obj.trigger_condition
            ),
            oracle_price_offset=obj.oracle_price_offset,
            auction_duration=obj.auction_duration,
            time_in_force=obj.time_in_force,
            auction_start_price=obj.auction_start_price,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "order_type": self.order_type.to_encodable(),
            "market_type": self.market_type.to_encodable(),
            "direction": self.direction.to_encodable(),
            "user_order_id": self.user_order_id,
            "base_asset_amount": self.base_asset_amount,
            "price": self.price,
            "market_index": self.market_index,
            "reduce_only": self.reduce_only,
            "post_only": self.post_only,
            "immediate_or_cancel": self.immediate_or_cancel,
            "trigger_price": self.trigger_price,
            "trigger_condition": self.trigger_condition.to_encodable(),
            "oracle_price_offset": self.oracle_price_offset,
            "auction_duration": self.auction_duration,
            "time_in_force": self.time_in_force,
            "auction_start_price": self.auction_start_price,
        }

    def to_json(self) -> OrderParamsJSON:
        return {
            "order_type": self.order_type.to_json(),
            "market_type": self.market_type.to_json(),
            "direction": self.direction.to_json(),
            "user_order_id": self.user_order_id,
            "base_asset_amount": self.base_asset_amount,
            "price": self.price,
            "market_index": self.market_index,
            "reduce_only": self.reduce_only,
            "post_only": self.post_only,
            "immediate_or_cancel": self.immediate_or_cancel,
            "trigger_price": self.trigger_price,
            "trigger_condition": self.trigger_condition.to_json(),
            "oracle_price_offset": self.oracle_price_offset,
            "auction_duration": self.auction_duration,
            "time_in_force": self.time_in_force,
            "auction_start_price": self.auction_start_price,
        }

    @classmethod
    def from_json(cls, obj: OrderParamsJSON) -> "OrderParams":
        return cls(
            order_type=order_type.from_json(obj["order_type"]),
            market_type=market_type.from_json(obj["market_type"]),
            direction=position_direction.from_json(obj["direction"]),
            user_order_id=obj["user_order_id"],
            base_asset_amount=obj["base_asset_amount"],
            price=obj["price"],
            market_index=obj["market_index"],
            reduce_only=obj["reduce_only"],
            post_only=obj["post_only"],
            immediate_or_cancel=obj["immediate_or_cancel"],
            trigger_price=obj["trigger_price"],
            trigger_condition=order_trigger_condition.from_json(
                obj["trigger_condition"]
            ),
            oracle_price_offset=obj["oracle_price_offset"],
            auction_duration=obj["auction_duration"],
            time_in_force=obj["time_in_force"],
            auction_start_price=obj["auction_start_price"],
        )
