import typing
from dataclasses import dataclass
from base64 import b64decode
from solana.publickey import PublicKey
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Commitment
import borsh_construct as borsh
from anchorpy.coder.accounts import ACCOUNT_DISCRIMINATOR_SIZE
from anchorpy.error import AccountInvalidDiscriminator
from anchorpy.utils.rpc import get_multiple_accounts
from anchorpy.borsh_extension import BorshPubkey
from ..program_id import PROGRAM_ID
from .. import types


class UserJSON(typing.TypedDict):
    authority: str
    delegate: str
    name: list[int]
    spot_positions: list[types.spot_position.SpotPositionJSON]
    perp_positions: list[types.perp_position.PerpPositionJSON]
    orders: list[types.order.OrderJSON]
    last_add_perp_lp_shares_ts: int
    total_deposits: int
    total_withdraws: int
    settled_perp_pnl: int
    cumulative_spot_fees: int
    next_order_id: int
    max_margin_ratio: int
    next_liquidation_id: int
    sub_account_id: int
    is_being_liquidated: bool
    is_bankrupt: bool
    is_margin_trading_enabled: bool
    padding: list[int]


@dataclass
class User:
    discriminator: typing.ClassVar = b"\x9fu_\xe3\xef\x97:\xec"
    layout: typing.ClassVar = borsh.CStruct(
        "authority" / BorshPubkey,
        "delegate" / BorshPubkey,
        "name" / borsh.U8[32],
        "spot_positions" / types.spot_position.SpotPosition.layout[8],
        "perp_positions" / types.perp_position.PerpPosition.layout[8],
        "orders" / types.order.Order.layout[32],
        "last_add_perp_lp_shares_ts" / borsh.I64,
        "total_deposits" / borsh.U64,
        "total_withdraws" / borsh.U64,
        "settled_perp_pnl" / borsh.I64,
        "cumulative_spot_fees" / borsh.I64,
        "next_order_id" / borsh.U32,
        "max_margin_ratio" / borsh.U32,
        "next_liquidation_id" / borsh.U16,
        "sub_account_id" / borsh.U8,
        "is_being_liquidated" / borsh.Bool,
        "is_bankrupt" / borsh.Bool,
        "is_margin_trading_enabled" / borsh.Bool,
        "padding" / borsh.U8[2],
    )
    authority: PublicKey
    delegate: PublicKey
    name: list[int]
    spot_positions: list[types.spot_position.SpotPosition]
    perp_positions: list[types.perp_position.PerpPosition]
    orders: list[types.order.Order]
    last_add_perp_lp_shares_ts: int
    total_deposits: int
    total_withdraws: int
    settled_perp_pnl: int
    cumulative_spot_fees: int
    next_order_id: int
    max_margin_ratio: int
    next_liquidation_id: int
    sub_account_id: int
    is_being_liquidated: bool
    is_bankrupt: bool
    is_margin_trading_enabled: bool
    padding: list[int]

    @classmethod
    async def fetch(
        cls,
        conn: AsyncClient,
        address: PublicKey,
        commitment: typing.Optional[Commitment] = None,
        program_id: PublicKey = PROGRAM_ID,
    ) -> typing.Optional["User"]:
        resp = await conn.get_account_info(address, commitment=commitment)
        info = resp["result"]["value"]
        if info is None:
            return None
        if info["owner"] != str(program_id):
            raise ValueError("Account does not belong to this program")
        bytes_data = b64decode(info["data"][0])
        return cls.decode(bytes_data)

    @classmethod
    async def fetch_multiple(
        cls,
        conn: AsyncClient,
        addresses: list[PublicKey],
        commitment: typing.Optional[Commitment] = None,
        program_id: PublicKey = PROGRAM_ID,
    ) -> typing.List[typing.Optional["User"]]:
        infos = await get_multiple_accounts(conn, addresses, commitment=commitment)
        res: typing.List[typing.Optional["User"]] = []
        for info in infos:
            if info is None:
                res.append(None)
                continue
            if info.account.owner != program_id:
                raise ValueError("Account does not belong to this program")
            res.append(cls.decode(info.account.data))
        return res

    @classmethod
    def decode(cls, data: bytes) -> "User":
        if data[:ACCOUNT_DISCRIMINATOR_SIZE] != cls.discriminator:
            raise AccountInvalidDiscriminator(
                "The discriminator for this account is invalid"
            )
        dec = User.layout.parse(data[ACCOUNT_DISCRIMINATOR_SIZE:])
        return cls(
            authority=dec.authority,
            delegate=dec.delegate,
            name=dec.name,
            spot_positions=list(
                map(
                    lambda item: types.spot_position.SpotPosition.from_decoded(item),
                    dec.spot_positions,
                )
            ),
            perp_positions=list(
                map(
                    lambda item: types.perp_position.PerpPosition.from_decoded(item),
                    dec.perp_positions,
                )
            ),
            orders=list(
                map(lambda item: types.order.Order.from_decoded(item), dec.orders)
            ),
            last_add_perp_lp_shares_ts=dec.last_add_perp_lp_shares_ts,
            total_deposits=dec.total_deposits,
            total_withdraws=dec.total_withdraws,
            settled_perp_pnl=dec.settled_perp_pnl,
            cumulative_spot_fees=dec.cumulative_spot_fees,
            next_order_id=dec.next_order_id,
            max_margin_ratio=dec.max_margin_ratio,
            next_liquidation_id=dec.next_liquidation_id,
            sub_account_id=dec.sub_account_id,
            is_being_liquidated=dec.is_being_liquidated,
            is_bankrupt=dec.is_bankrupt,
            is_margin_trading_enabled=dec.is_margin_trading_enabled,
            padding=dec.padding,
        )

    def to_json(self) -> UserJSON:
        return {
            "authority": str(self.authority),
            "delegate": str(self.delegate),
            "name": self.name,
            "spot_positions": list(
                map(lambda item: item.to_json(), self.spot_positions)
            ),
            "perp_positions": list(
                map(lambda item: item.to_json(), self.perp_positions)
            ),
            "orders": list(map(lambda item: item.to_json(), self.orders)),
            "last_add_perp_lp_shares_ts": self.last_add_perp_lp_shares_ts,
            "total_deposits": self.total_deposits,
            "total_withdraws": self.total_withdraws,
            "settled_perp_pnl": self.settled_perp_pnl,
            "cumulative_spot_fees": self.cumulative_spot_fees,
            "next_order_id": self.next_order_id,
            "max_margin_ratio": self.max_margin_ratio,
            "next_liquidation_id": self.next_liquidation_id,
            "sub_account_id": self.sub_account_id,
            "is_being_liquidated": self.is_being_liquidated,
            "is_bankrupt": self.is_bankrupt,
            "is_margin_trading_enabled": self.is_margin_trading_enabled,
            "padding": self.padding,
        }

    @classmethod
    def from_json(cls, obj: UserJSON) -> "User":
        return cls(
            authority=PublicKey(obj["authority"]),
            delegate=PublicKey(obj["delegate"]),
            name=obj["name"],
            spot_positions=list(
                map(
                    lambda item: types.spot_position.SpotPosition.from_json(item),
                    obj["spot_positions"],
                )
            ),
            perp_positions=list(
                map(
                    lambda item: types.perp_position.PerpPosition.from_json(item),
                    obj["perp_positions"],
                )
            ),
            orders=list(
                map(lambda item: types.order.Order.from_json(item), obj["orders"])
            ),
            last_add_perp_lp_shares_ts=obj["last_add_perp_lp_shares_ts"],
            total_deposits=obj["total_deposits"],
            total_withdraws=obj["total_withdraws"],
            settled_perp_pnl=obj["settled_perp_pnl"],
            cumulative_spot_fees=obj["cumulative_spot_fees"],
            next_order_id=obj["next_order_id"],
            max_margin_ratio=obj["max_margin_ratio"],
            next_liquidation_id=obj["next_liquidation_id"],
            sub_account_id=obj["sub_account_id"],
            is_being_liquidated=obj["is_being_liquidated"],
            is_bankrupt=obj["is_bankrupt"],
            is_margin_trading_enabled=obj["is_margin_trading_enabled"],
            padding=obj["padding"],
        )
