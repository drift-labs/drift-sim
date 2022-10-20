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


class SerumV3FulfillmentConfigJSON(typing.TypedDict):
    pubkey: str
    serum_program_id: str
    serum_market: str
    serum_request_queue: str
    serum_event_queue: str
    serum_bids: str
    serum_asks: str
    serum_base_vault: str
    serum_quote_vault: str
    serum_open_orders: str
    serum_signer_nonce: int
    market_index: int
    fulfillment_type: types.spot_fulfillment_type.SpotFulfillmentTypeJSON
    status: types.spot_fulfillment_status.SpotFulfillmentStatusJSON
    padding: list[int]


@dataclass
class SerumV3FulfillmentConfig:
    discriminator: typing.ClassVar = b"A\xa0\xc5p\xef\xa8g\xb9"
    layout: typing.ClassVar = borsh.CStruct(
        "pubkey" / BorshPubkey,
        "serum_program_id" / BorshPubkey,
        "serum_market" / BorshPubkey,
        "serum_request_queue" / BorshPubkey,
        "serum_event_queue" / BorshPubkey,
        "serum_bids" / BorshPubkey,
        "serum_asks" / BorshPubkey,
        "serum_base_vault" / BorshPubkey,
        "serum_quote_vault" / BorshPubkey,
        "serum_open_orders" / BorshPubkey,
        "serum_signer_nonce" / borsh.U64,
        "market_index" / borsh.U16,
        "fulfillment_type" / types.spot_fulfillment_type.layout,
        "status" / types.spot_fulfillment_status.layout,
        "padding" / borsh.U8[4],
    )
    pubkey: PublicKey
    serum_program_id: PublicKey
    serum_market: PublicKey
    serum_request_queue: PublicKey
    serum_event_queue: PublicKey
    serum_bids: PublicKey
    serum_asks: PublicKey
    serum_base_vault: PublicKey
    serum_quote_vault: PublicKey
    serum_open_orders: PublicKey
    serum_signer_nonce: int
    market_index: int
    fulfillment_type: types.spot_fulfillment_type.SpotFulfillmentTypeKind
    status: types.spot_fulfillment_status.SpotFulfillmentStatusKind
    padding: list[int]

    @classmethod
    async def fetch(
        cls,
        conn: AsyncClient,
        address: PublicKey,
        commitment: typing.Optional[Commitment] = None,
        program_id: PublicKey = PROGRAM_ID,
    ) -> typing.Optional["SerumV3FulfillmentConfig"]:
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
    ) -> typing.List[typing.Optional["SerumV3FulfillmentConfig"]]:
        infos = await get_multiple_accounts(conn, addresses, commitment=commitment)
        res: typing.List[typing.Optional["SerumV3FulfillmentConfig"]] = []
        for info in infos:
            if info is None:
                res.append(None)
                continue
            if info.account.owner != program_id:
                raise ValueError("Account does not belong to this program")
            res.append(cls.decode(info.account.data))
        return res

    @classmethod
    def decode(cls, data: bytes) -> "SerumV3FulfillmentConfig":
        if data[:ACCOUNT_DISCRIMINATOR_SIZE] != cls.discriminator:
            raise AccountInvalidDiscriminator(
                "The discriminator for this account is invalid"
            )
        dec = SerumV3FulfillmentConfig.layout.parse(data[ACCOUNT_DISCRIMINATOR_SIZE:])
        return cls(
            pubkey=dec.pubkey,
            serum_program_id=dec.serum_program_id,
            serum_market=dec.serum_market,
            serum_request_queue=dec.serum_request_queue,
            serum_event_queue=dec.serum_event_queue,
            serum_bids=dec.serum_bids,
            serum_asks=dec.serum_asks,
            serum_base_vault=dec.serum_base_vault,
            serum_quote_vault=dec.serum_quote_vault,
            serum_open_orders=dec.serum_open_orders,
            serum_signer_nonce=dec.serum_signer_nonce,
            market_index=dec.market_index,
            fulfillment_type=types.spot_fulfillment_type.from_decoded(
                dec.fulfillment_type
            ),
            status=types.spot_fulfillment_status.from_decoded(dec.status),
            padding=dec.padding,
        )

    def to_json(self) -> SerumV3FulfillmentConfigJSON:
        return {
            "pubkey": str(self.pubkey),
            "serum_program_id": str(self.serum_program_id),
            "serum_market": str(self.serum_market),
            "serum_request_queue": str(self.serum_request_queue),
            "serum_event_queue": str(self.serum_event_queue),
            "serum_bids": str(self.serum_bids),
            "serum_asks": str(self.serum_asks),
            "serum_base_vault": str(self.serum_base_vault),
            "serum_quote_vault": str(self.serum_quote_vault),
            "serum_open_orders": str(self.serum_open_orders),
            "serum_signer_nonce": self.serum_signer_nonce,
            "market_index": self.market_index,
            "fulfillment_type": self.fulfillment_type.to_json(),
            "status": self.status.to_json(),
            "padding": self.padding,
        }

    @classmethod
    def from_json(cls, obj: SerumV3FulfillmentConfigJSON) -> "SerumV3FulfillmentConfig":
        return cls(
            pubkey=PublicKey(obj["pubkey"]),
            serum_program_id=PublicKey(obj["serum_program_id"]),
            serum_market=PublicKey(obj["serum_market"]),
            serum_request_queue=PublicKey(obj["serum_request_queue"]),
            serum_event_queue=PublicKey(obj["serum_event_queue"]),
            serum_bids=PublicKey(obj["serum_bids"]),
            serum_asks=PublicKey(obj["serum_asks"]),
            serum_base_vault=PublicKey(obj["serum_base_vault"]),
            serum_quote_vault=PublicKey(obj["serum_quote_vault"]),
            serum_open_orders=PublicKey(obj["serum_open_orders"]),
            serum_signer_nonce=obj["serum_signer_nonce"],
            market_index=obj["market_index"],
            fulfillment_type=types.spot_fulfillment_type.from_json(
                obj["fulfillment_type"]
            ),
            status=types.spot_fulfillment_status.from_json(obj["status"]),
            padding=obj["padding"],
        )
