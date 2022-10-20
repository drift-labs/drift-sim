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


class InsuranceFundStakeJSON(typing.TypedDict):
    authority: str
    if_shares: int
    last_withdraw_request_shares: int
    if_base: int
    last_valid_ts: int
    last_withdraw_request_value: int
    last_withdraw_request_ts: int
    market_index: int
    cost_basis: int
    padding: list[int]


@dataclass
class InsuranceFundStake:
    discriminator: typing.ClassVar = b"n\xca\x0e*_IZ_"
    layout: typing.ClassVar = borsh.CStruct(
        "authority" / BorshPubkey,
        "if_shares" / borsh.U128,
        "last_withdraw_request_shares" / borsh.U128,
        "if_base" / borsh.U128,
        "last_valid_ts" / borsh.I64,
        "last_withdraw_request_value" / borsh.U64,
        "last_withdraw_request_ts" / borsh.I64,
        "market_index" / borsh.U16,
        "cost_basis" / borsh.I64,
        "padding" / borsh.U8[6],
    )
    authority: PublicKey
    if_shares: int
    last_withdraw_request_shares: int
    if_base: int
    last_valid_ts: int
    last_withdraw_request_value: int
    last_withdraw_request_ts: int
    market_index: int
    cost_basis: int
    padding: list[int]

    @classmethod
    async def fetch(
        cls,
        conn: AsyncClient,
        address: PublicKey,
        commitment: typing.Optional[Commitment] = None,
        program_id: PublicKey = PROGRAM_ID,
    ) -> typing.Optional["InsuranceFundStake"]:
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
    ) -> typing.List[typing.Optional["InsuranceFundStake"]]:
        infos = await get_multiple_accounts(conn, addresses, commitment=commitment)
        res: typing.List[typing.Optional["InsuranceFundStake"]] = []
        for info in infos:
            if info is None:
                res.append(None)
                continue
            if info.account.owner != program_id:
                raise ValueError("Account does not belong to this program")
            res.append(cls.decode(info.account.data))
        return res

    @classmethod
    def decode(cls, data: bytes) -> "InsuranceFundStake":
        if data[:ACCOUNT_DISCRIMINATOR_SIZE] != cls.discriminator:
            raise AccountInvalidDiscriminator(
                "The discriminator for this account is invalid"
            )
        dec = InsuranceFundStake.layout.parse(data[ACCOUNT_DISCRIMINATOR_SIZE:])
        return cls(
            authority=dec.authority,
            if_shares=dec.if_shares,
            last_withdraw_request_shares=dec.last_withdraw_request_shares,
            if_base=dec.if_base,
            last_valid_ts=dec.last_valid_ts,
            last_withdraw_request_value=dec.last_withdraw_request_value,
            last_withdraw_request_ts=dec.last_withdraw_request_ts,
            market_index=dec.market_index,
            cost_basis=dec.cost_basis,
            padding=dec.padding,
        )

    def to_json(self) -> InsuranceFundStakeJSON:
        return {
            "authority": str(self.authority),
            "if_shares": self.if_shares,
            "last_withdraw_request_shares": self.last_withdraw_request_shares,
            "if_base": self.if_base,
            "last_valid_ts": self.last_valid_ts,
            "last_withdraw_request_value": self.last_withdraw_request_value,
            "last_withdraw_request_ts": self.last_withdraw_request_ts,
            "market_index": self.market_index,
            "cost_basis": self.cost_basis,
            "padding": self.padding,
        }

    @classmethod
    def from_json(cls, obj: InsuranceFundStakeJSON) -> "InsuranceFundStake":
        return cls(
            authority=PublicKey(obj["authority"]),
            if_shares=obj["if_shares"],
            last_withdraw_request_shares=obj["last_withdraw_request_shares"],
            if_base=obj["if_base"],
            last_valid_ts=obj["last_valid_ts"],
            last_withdraw_request_value=obj["last_withdraw_request_value"],
            last_withdraw_request_ts=obj["last_withdraw_request_ts"],
            market_index=obj["market_index"],
            cost_basis=obj["cost_basis"],
            padding=obj["padding"],
        )
