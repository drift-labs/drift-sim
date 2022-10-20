from __future__ import annotations
from . import (
    position_direction,
    order_status,
    order_type,
    order_trigger_condition,
    market_type,
)
import typing
from dataclasses import dataclass
from construct import Container
import borsh_construct as borsh


class OrderJSON(typing.TypedDict):
    ts: int
    slot: int
    price: int
    base_asset_amount: int
    base_asset_amount_filled: int
    quote_asset_amount_filled: int
    trigger_price: int
    auction_start_price: int
    auction_end_price: int
    oracle_price_offset: int
    order_id: int
    market_index: int
    status: order_status.OrderStatusJSON
    order_type: order_type.OrderTypeJSON
    market_type: market_type.MarketTypeJSON
    user_order_id: int
    existing_position_direction: position_direction.PositionDirectionJSON
    direction: position_direction.PositionDirectionJSON
    reduce_only: bool
    post_only: bool
    immediate_or_cancel: bool
    trigger_condition: order_trigger_condition.OrderTriggerConditionJSON
    triggered: bool
    auction_duration: int
    time_in_force: int
    padding: list[int]


@dataclass
class Order:
    layout: typing.ClassVar = borsh.CStruct(
        "ts" / borsh.I64,
        "slot" / borsh.U64,
        "price" / borsh.U64,
        "base_asset_amount" / borsh.U64,
        "base_asset_amount_filled" / borsh.U64,
        "quote_asset_amount_filled" / borsh.U64,
        "trigger_price" / borsh.U64,
        "auction_start_price" / borsh.U64,
        "auction_end_price" / borsh.U64,
        "oracle_price_offset" / borsh.I32,
        "order_id" / borsh.U32,
        "market_index" / borsh.U16,
        "status" / order_status.layout,
        "order_type" / order_type.layout,
        "market_type" / market_type.layout,
        "user_order_id" / borsh.U8,
        "existing_position_direction" / position_direction.layout,
        "direction" / position_direction.layout,
        "reduce_only" / borsh.Bool,
        "post_only" / borsh.Bool,
        "immediate_or_cancel" / borsh.Bool,
        "trigger_condition" / order_trigger_condition.layout,
        "triggered" / borsh.Bool,
        "auction_duration" / borsh.U8,
        "time_in_force" / borsh.U8,
        "padding" / borsh.U8[1],
    )
    ts: int
    slot: int
    price: int
    base_asset_amount: int
    base_asset_amount_filled: int
    quote_asset_amount_filled: int
    trigger_price: int
    auction_start_price: int
    auction_end_price: int
    oracle_price_offset: int
    order_id: int
    market_index: int
    status: order_status.OrderStatusKind
    order_type: order_type.OrderTypeKind
    market_type: market_type.MarketTypeKind
    user_order_id: int
    existing_position_direction: position_direction.PositionDirectionKind
    direction: position_direction.PositionDirectionKind
    reduce_only: bool
    post_only: bool
    immediate_or_cancel: bool
    trigger_condition: order_trigger_condition.OrderTriggerConditionKind
    triggered: bool
    auction_duration: int
    time_in_force: int
    padding: list[int]

    @classmethod
    def from_decoded(cls, obj: Container) -> "Order":
        return cls(
            ts=obj.ts,
            slot=obj.slot,
            price=obj.price,
            base_asset_amount=obj.base_asset_amount,
            base_asset_amount_filled=obj.base_asset_amount_filled,
            quote_asset_amount_filled=obj.quote_asset_amount_filled,
            trigger_price=obj.trigger_price,
            auction_start_price=obj.auction_start_price,
            auction_end_price=obj.auction_end_price,
            oracle_price_offset=obj.oracle_price_offset,
            order_id=obj.order_id,
            market_index=obj.market_index,
            status=order_status.from_decoded(obj.status),
            order_type=order_type.from_decoded(obj.order_type),
            market_type=market_type.from_decoded(obj.market_type),
            user_order_id=obj.user_order_id,
            existing_position_direction=position_direction.from_decoded(
                obj.existing_position_direction
            ),
            direction=position_direction.from_decoded(obj.direction),
            reduce_only=obj.reduce_only,
            post_only=obj.post_only,
            immediate_or_cancel=obj.immediate_or_cancel,
            trigger_condition=order_trigger_condition.from_decoded(
                obj.trigger_condition
            ),
            triggered=obj.triggered,
            auction_duration=obj.auction_duration,
            time_in_force=obj.time_in_force,
            padding=obj.padding,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "ts": self.ts,
            "slot": self.slot,
            "price": self.price,
            "base_asset_amount": self.base_asset_amount,
            "base_asset_amount_filled": self.base_asset_amount_filled,
            "quote_asset_amount_filled": self.quote_asset_amount_filled,
            "trigger_price": self.trigger_price,
            "auction_start_price": self.auction_start_price,
            "auction_end_price": self.auction_end_price,
            "oracle_price_offset": self.oracle_price_offset,
            "order_id": self.order_id,
            "market_index": self.market_index,
            "status": self.status.to_encodable(),
            "order_type": self.order_type.to_encodable(),
            "market_type": self.market_type.to_encodable(),
            "user_order_id": self.user_order_id,
            "existing_position_direction": self.existing_position_direction.to_encodable(),
            "direction": self.direction.to_encodable(),
            "reduce_only": self.reduce_only,
            "post_only": self.post_only,
            "immediate_or_cancel": self.immediate_or_cancel,
            "trigger_condition": self.trigger_condition.to_encodable(),
            "triggered": self.triggered,
            "auction_duration": self.auction_duration,
            "time_in_force": self.time_in_force,
            "padding": self.padding,
        }

    def to_json(self) -> OrderJSON:
        return {
            "ts": self.ts,
            "slot": self.slot,
            "price": self.price,
            "base_asset_amount": self.base_asset_amount,
            "base_asset_amount_filled": self.base_asset_amount_filled,
            "quote_asset_amount_filled": self.quote_asset_amount_filled,
            "trigger_price": self.trigger_price,
            "auction_start_price": self.auction_start_price,
            "auction_end_price": self.auction_end_price,
            "oracle_price_offset": self.oracle_price_offset,
            "order_id": self.order_id,
            "market_index": self.market_index,
            "status": self.status.to_json(),
            "order_type": self.order_type.to_json(),
            "market_type": self.market_type.to_json(),
            "user_order_id": self.user_order_id,
            "existing_position_direction": self.existing_position_direction.to_json(),
            "direction": self.direction.to_json(),
            "reduce_only": self.reduce_only,
            "post_only": self.post_only,
            "immediate_or_cancel": self.immediate_or_cancel,
            "trigger_condition": self.trigger_condition.to_json(),
            "triggered": self.triggered,
            "auction_duration": self.auction_duration,
            "time_in_force": self.time_in_force,
            "padding": self.padding,
        }

    @classmethod
    def from_json(cls, obj: OrderJSON) -> "Order":
        return cls(
            ts=obj["ts"],
            slot=obj["slot"],
            price=obj["price"],
            base_asset_amount=obj["base_asset_amount"],
            base_asset_amount_filled=obj["base_asset_amount_filled"],
            quote_asset_amount_filled=obj["quote_asset_amount_filled"],
            trigger_price=obj["trigger_price"],
            auction_start_price=obj["auction_start_price"],
            auction_end_price=obj["auction_end_price"],
            oracle_price_offset=obj["oracle_price_offset"],
            order_id=obj["order_id"],
            market_index=obj["market_index"],
            status=order_status.from_json(obj["status"]),
            order_type=order_type.from_json(obj["order_type"]),
            market_type=market_type.from_json(obj["market_type"]),
            user_order_id=obj["user_order_id"],
            existing_position_direction=position_direction.from_json(
                obj["existing_position_direction"]
            ),
            direction=position_direction.from_json(obj["direction"]),
            reduce_only=obj["reduce_only"],
            post_only=obj["post_only"],
            immediate_or_cancel=obj["immediate_or_cancel"],
            trigger_condition=order_trigger_condition.from_json(
                obj["trigger_condition"]
            ),
            triggered=obj["triggered"],
            auction_duration=obj["auction_duration"],
            time_in_force=obj["time_in_force"],
            padding=obj["padding"],
        )
