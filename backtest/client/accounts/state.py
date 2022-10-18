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


class StateJSON(typing.TypedDict):
    admin: str
    whitelist_mint: str
    discount_mint: str
    signer: str
    srm_vault: str
    perp_fee_structure: types.fee_structure.FeeStructureJSON
    spot_fee_structure: types.fee_structure.FeeStructureJSON
    oracle_guard_rails: types.oracle_guard_rails.OracleGuardRailsJSON
    number_of_authorities: int
    lp_cooldown_time: int
    liquidation_margin_buffer_ratio: int
    settlement_duration: int
    number_of_markets: int
    number_of_spot_markets: int
    signer_nonce: int
    min_perp_auction_duration: int
    default_market_order_time_in_force: int
    default_spot_auction_duration: int
    exchange_status: types.exchange_status.ExchangeStatusJSON
    padding: list[int]


@dataclass
class State:
    discriminator: typing.ClassVar = b"\xd8\x92k^hK\xb6\xb1"
    layout: typing.ClassVar = borsh.CStruct(
        "admin" / BorshPubkey,
        "whitelist_mint" / BorshPubkey,
        "discount_mint" / BorshPubkey,
        "signer" / BorshPubkey,
        "srm_vault" / BorshPubkey,
        "perp_fee_structure" / types.fee_structure.FeeStructure.layout,
        "spot_fee_structure" / types.fee_structure.FeeStructure.layout,
        "oracle_guard_rails" / types.oracle_guard_rails.OracleGuardRails.layout,
        "number_of_authorities" / borsh.U64,
        "lp_cooldown_time" / borsh.U64,
        "liquidation_margin_buffer_ratio" / borsh.U32,
        "settlement_duration" / borsh.U16,
        "number_of_markets" / borsh.U16,
        "number_of_spot_markets" / borsh.U16,
        "signer_nonce" / borsh.U8,
        "min_perp_auction_duration" / borsh.U8,
        "default_market_order_time_in_force" / borsh.U8,
        "default_spot_auction_duration" / borsh.U8,
        "exchange_status" / types.exchange_status.layout,
        "padding" / borsh.U8[1],
    )
    admin: PublicKey
    whitelist_mint: PublicKey
    discount_mint: PublicKey
    signer: PublicKey
    srm_vault: PublicKey
    perp_fee_structure: types.fee_structure.FeeStructure
    spot_fee_structure: types.fee_structure.FeeStructure
    oracle_guard_rails: types.oracle_guard_rails.OracleGuardRails
    number_of_authorities: int
    lp_cooldown_time: int
    liquidation_margin_buffer_ratio: int
    settlement_duration: int
    number_of_markets: int
    number_of_spot_markets: int
    signer_nonce: int
    min_perp_auction_duration: int
    default_market_order_time_in_force: int
    default_spot_auction_duration: int
    exchange_status: types.exchange_status.ExchangeStatusKind
    padding: list[int]

    @classmethod
    async def fetch(
        cls,
        conn: AsyncClient,
        address: PublicKey,
        commitment: typing.Optional[Commitment] = None,
        program_id: PublicKey = PROGRAM_ID,
    ) -> typing.Optional["State"]:
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
    ) -> typing.List[typing.Optional["State"]]:
        infos = await get_multiple_accounts(conn, addresses, commitment=commitment)
        res: typing.List[typing.Optional["State"]] = []
        for info in infos:
            if info is None:
                res.append(None)
                continue
            if info.account.owner != program_id:
                raise ValueError("Account does not belong to this program")
            res.append(cls.decode(info.account.data))
        return res

    @classmethod
    def decode(cls, data: bytes) -> "State":
        if data[:ACCOUNT_DISCRIMINATOR_SIZE] != cls.discriminator:
            raise AccountInvalidDiscriminator(
                "The discriminator for this account is invalid"
            )
        dec = State.layout.parse(data[ACCOUNT_DISCRIMINATOR_SIZE:])
        return cls(
            admin=dec.admin,
            whitelist_mint=dec.whitelist_mint,
            discount_mint=dec.discount_mint,
            signer=dec.signer,
            srm_vault=dec.srm_vault,
            perp_fee_structure=types.fee_structure.FeeStructure.from_decoded(
                dec.perp_fee_structure
            ),
            spot_fee_structure=types.fee_structure.FeeStructure.from_decoded(
                dec.spot_fee_structure
            ),
            oracle_guard_rails=types.oracle_guard_rails.OracleGuardRails.from_decoded(
                dec.oracle_guard_rails
            ),
            number_of_authorities=dec.number_of_authorities,
            lp_cooldown_time=dec.lp_cooldown_time,
            liquidation_margin_buffer_ratio=dec.liquidation_margin_buffer_ratio,
            settlement_duration=dec.settlement_duration,
            number_of_markets=dec.number_of_markets,
            number_of_spot_markets=dec.number_of_spot_markets,
            signer_nonce=dec.signer_nonce,
            min_perp_auction_duration=dec.min_perp_auction_duration,
            default_market_order_time_in_force=dec.default_market_order_time_in_force,
            default_spot_auction_duration=dec.default_spot_auction_duration,
            exchange_status=types.exchange_status.from_decoded(dec.exchange_status),
            padding=dec.padding,
        )

    def to_json(self) -> StateJSON:
        return {
            "admin": str(self.admin),
            "whitelist_mint": str(self.whitelist_mint),
            "discount_mint": str(self.discount_mint),
            "signer": str(self.signer),
            "srm_vault": str(self.srm_vault),
            "perp_fee_structure": self.perp_fee_structure.to_json(),
            "spot_fee_structure": self.spot_fee_structure.to_json(),
            "oracle_guard_rails": self.oracle_guard_rails.to_json(),
            "number_of_authorities": self.number_of_authorities,
            "lp_cooldown_time": self.lp_cooldown_time,
            "liquidation_margin_buffer_ratio": self.liquidation_margin_buffer_ratio,
            "settlement_duration": self.settlement_duration,
            "number_of_markets": self.number_of_markets,
            "number_of_spot_markets": self.number_of_spot_markets,
            "signer_nonce": self.signer_nonce,
            "min_perp_auction_duration": self.min_perp_auction_duration,
            "default_market_order_time_in_force": self.default_market_order_time_in_force,
            "default_spot_auction_duration": self.default_spot_auction_duration,
            "exchange_status": self.exchange_status.to_json(),
            "padding": self.padding,
        }

    @classmethod
    def from_json(cls, obj: StateJSON) -> "State":
        return cls(
            admin=PublicKey(obj["admin"]),
            whitelist_mint=PublicKey(obj["whitelist_mint"]),
            discount_mint=PublicKey(obj["discount_mint"]),
            signer=PublicKey(obj["signer"]),
            srm_vault=PublicKey(obj["srm_vault"]),
            perp_fee_structure=types.fee_structure.FeeStructure.from_json(
                obj["perp_fee_structure"]
            ),
            spot_fee_structure=types.fee_structure.FeeStructure.from_json(
                obj["spot_fee_structure"]
            ),
            oracle_guard_rails=types.oracle_guard_rails.OracleGuardRails.from_json(
                obj["oracle_guard_rails"]
            ),
            number_of_authorities=obj["number_of_authorities"],
            lp_cooldown_time=obj["lp_cooldown_time"],
            liquidation_margin_buffer_ratio=obj["liquidation_margin_buffer_ratio"],
            settlement_duration=obj["settlement_duration"],
            number_of_markets=obj["number_of_markets"],
            number_of_spot_markets=obj["number_of_spot_markets"],
            signer_nonce=obj["signer_nonce"],
            min_perp_auction_duration=obj["min_perp_auction_duration"],
            default_market_order_time_in_force=obj[
                "default_market_order_time_in_force"
            ],
            default_spot_auction_duration=obj["default_spot_auction_duration"],
            exchange_status=types.exchange_status.from_json(obj["exchange_status"]),
            padding=obj["padding"],
        )
