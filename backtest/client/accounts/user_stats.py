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


class UserStatsJSON(typing.TypedDict):
    authority: str
    referrer: str
    fees: types.user_fees.UserFeesJSON
    next_epoch_ts: int
    maker_volume30d: int
    taker_volume30d: int
    filler_volume30d: int
    last_maker_volume30d_ts: int
    last_taker_volume30d_ts: int
    last_filler_volume30d_ts: int
    if_staked_quote_asset_amount: int
    number_of_sub_accounts: int
    is_referrer: bool
    padding: list[int]


@dataclass
class UserStats:
    discriminator: typing.ClassVar = b"\xb0\xdf\x88\x1bzO \xe3"
    layout: typing.ClassVar = borsh.CStruct(
        "authority" / BorshPubkey,
        "referrer" / BorshPubkey,
        "fees" / types.user_fees.UserFees.layout,
        "next_epoch_ts" / borsh.I64,
        "maker_volume30d" / borsh.U64,
        "taker_volume30d" / borsh.U64,
        "filler_volume30d" / borsh.U64,
        "last_maker_volume30d_ts" / borsh.I64,
        "last_taker_volume30d_ts" / borsh.I64,
        "last_filler_volume30d_ts" / borsh.I64,
        "if_staked_quote_asset_amount" / borsh.U64,
        "number_of_sub_accounts" / borsh.U8,
        "is_referrer" / borsh.Bool,
        "padding" / borsh.U8[6],
    )
    authority: PublicKey
    referrer: PublicKey
    fees: types.user_fees.UserFees
    next_epoch_ts: int
    maker_volume30d: int
    taker_volume30d: int
    filler_volume30d: int
    last_maker_volume30d_ts: int
    last_taker_volume30d_ts: int
    last_filler_volume30d_ts: int
    if_staked_quote_asset_amount: int
    number_of_sub_accounts: int
    is_referrer: bool
    padding: list[int]

    @classmethod
    async def fetch(
        cls,
        conn: AsyncClient,
        address: PublicKey,
        commitment: typing.Optional[Commitment] = None,
        program_id: PublicKey = PROGRAM_ID,
    ) -> typing.Optional["UserStats"]:
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
    ) -> typing.List[typing.Optional["UserStats"]]:
        infos = await get_multiple_accounts(conn, addresses, commitment=commitment)
        res: typing.List[typing.Optional["UserStats"]] = []
        for info in infos:
            if info is None:
                res.append(None)
                continue
            if info.account.owner != program_id:
                raise ValueError("Account does not belong to this program")
            res.append(cls.decode(info.account.data))
        return res

    @classmethod
    def decode(cls, data: bytes) -> "UserStats":
        if data[:ACCOUNT_DISCRIMINATOR_SIZE] != cls.discriminator:
            raise AccountInvalidDiscriminator(
                "The discriminator for this account is invalid"
            )
        dec = UserStats.layout.parse(data[ACCOUNT_DISCRIMINATOR_SIZE:])
        return cls(
            authority=dec.authority,
            referrer=dec.referrer,
            fees=types.user_fees.UserFees.from_decoded(dec.fees),
            next_epoch_ts=dec.next_epoch_ts,
            maker_volume30d=dec.maker_volume30d,
            taker_volume30d=dec.taker_volume30d,
            filler_volume30d=dec.filler_volume30d,
            last_maker_volume30d_ts=dec.last_maker_volume30d_ts,
            last_taker_volume30d_ts=dec.last_taker_volume30d_ts,
            last_filler_volume30d_ts=dec.last_filler_volume30d_ts,
            if_staked_quote_asset_amount=dec.if_staked_quote_asset_amount,
            number_of_sub_accounts=dec.number_of_sub_accounts,
            is_referrer=dec.is_referrer,
            padding=dec.padding,
        )

    def to_json(self) -> UserStatsJSON:
        return {
            "authority": str(self.authority),
            "referrer": str(self.referrer),
            "fees": self.fees.to_json(),
            "next_epoch_ts": self.next_epoch_ts,
            "maker_volume30d": self.maker_volume30d,
            "taker_volume30d": self.taker_volume30d,
            "filler_volume30d": self.filler_volume30d,
            "last_maker_volume30d_ts": self.last_maker_volume30d_ts,
            "last_taker_volume30d_ts": self.last_taker_volume30d_ts,
            "last_filler_volume30d_ts": self.last_filler_volume30d_ts,
            "if_staked_quote_asset_amount": self.if_staked_quote_asset_amount,
            "number_of_sub_accounts": self.number_of_sub_accounts,
            "is_referrer": self.is_referrer,
            "padding": self.padding,
        }

    @classmethod
    def from_json(cls, obj: UserStatsJSON) -> "UserStats":
        return cls(
            authority=PublicKey(obj["authority"]),
            referrer=PublicKey(obj["referrer"]),
            fees=types.user_fees.UserFees.from_json(obj["fees"]),
            next_epoch_ts=obj["next_epoch_ts"],
            maker_volume30d=obj["maker_volume30d"],
            taker_volume30d=obj["taker_volume30d"],
            filler_volume30d=obj["filler_volume30d"],
            last_maker_volume30d_ts=obj["last_maker_volume30d_ts"],
            last_taker_volume30d_ts=obj["last_taker_volume30d_ts"],
            last_filler_volume30d_ts=obj["last_filler_volume30d_ts"],
            if_staked_quote_asset_amount=obj["if_staked_quote_asset_amount"],
            number_of_sub_accounts=obj["number_of_sub_accounts"],
            is_referrer=obj["is_referrer"],
            padding=obj["padding"],
        )
