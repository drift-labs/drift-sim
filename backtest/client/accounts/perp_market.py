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


class PerpMarketJSON(typing.TypedDict):
    pubkey: str
    amm: types.amm.AMMJSON
    pnl_pool: types.pool_balance.PoolBalanceJSON
    name: list[int]
    expiry_price: int
    number_of_users: int
    imf_factor: int
    unrealized_pnl_imf_factor: int
    unrealized_pnl_max_imbalance: int
    liquidator_fee: int
    if_liquidation_fee: int
    insurance_claim: types.insurance_claim.InsuranceClaimJSON
    expiry_ts: int
    next_fill_record_id: int
    next_funding_rate_record_id: int
    next_curve_record_id: int
    margin_ratio_initial: int
    margin_ratio_maintenance: int
    unrealized_pnl_initial_asset_weight: int
    unrealized_pnl_maintenance_asset_weight: int
    market_index: int
    status: types.market_status.MarketStatusJSON
    contract_type: types.contract_type.ContractTypeJSON
    contract_tier: types.contract_tier.ContractTierJSON
    padding: list[int]


@dataclass
class PerpMarket:
    discriminator: typing.ClassVar = b"\n\xdf\x0c,k\xf57\xf7"
    layout: typing.ClassVar = borsh.CStruct(
        "pubkey" / BorshPubkey,
        "amm" / types.amm.AMM.layout,
        "pnl_pool" / types.pool_balance.PoolBalance.layout,
        "name" / borsh.U8[32],
        "expiry_price" / borsh.I128,
        "number_of_users" / borsh.U128,
        "imf_factor" / borsh.U128,
        "unrealized_pnl_imf_factor" / borsh.U128,
        "unrealized_pnl_max_imbalance" / borsh.U128,
        "liquidator_fee" / borsh.U128,
        "if_liquidation_fee" / borsh.U128,
        "insurance_claim" / types.insurance_claim.InsuranceClaim.layout,
        "expiry_ts" / borsh.I64,
        "next_fill_record_id" / borsh.U64,
        "next_funding_rate_record_id" / borsh.U64,
        "next_curve_record_id" / borsh.U64,
        "margin_ratio_initial" / borsh.U32,
        "margin_ratio_maintenance" / borsh.U32,
        "unrealized_pnl_initial_asset_weight" / borsh.U32,
        "unrealized_pnl_maintenance_asset_weight" / borsh.U32,
        "market_index" / borsh.U16,
        "status" / types.market_status.layout,
        "contract_type" / types.contract_type.layout,
        "contract_tier" / types.contract_tier.layout,
        "padding" / borsh.U8[3],
    )
    pubkey: PublicKey
    amm: types.amm.AMM
    pnl_pool: types.pool_balance.PoolBalance
    name: list[int]
    expiry_price: int
    number_of_users: int
    imf_factor: int
    unrealized_pnl_imf_factor: int
    unrealized_pnl_max_imbalance: int
    liquidator_fee: int
    if_liquidation_fee: int
    insurance_claim: types.insurance_claim.InsuranceClaim
    expiry_ts: int
    next_fill_record_id: int
    next_funding_rate_record_id: int
    next_curve_record_id: int
    margin_ratio_initial: int
    margin_ratio_maintenance: int
    unrealized_pnl_initial_asset_weight: int
    unrealized_pnl_maintenance_asset_weight: int
    market_index: int
    status: types.market_status.MarketStatusKind
    contract_type: types.contract_type.ContractTypeKind
    contract_tier: types.contract_tier.ContractTierKind
    padding: list[int]

    @classmethod
    async def fetch(
        cls,
        conn: AsyncClient,
        address: PublicKey,
        commitment: typing.Optional[Commitment] = None,
        program_id: PublicKey = PROGRAM_ID,
    ) -> typing.Optional["PerpMarket"]:
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
    ) -> typing.List[typing.Optional["PerpMarket"]]:
        infos = await get_multiple_accounts(conn, addresses, commitment=commitment)
        res: typing.List[typing.Optional["PerpMarket"]] = []
        for info in infos:
            if info is None:
                res.append(None)
                continue
            if info.account.owner != program_id:
                raise ValueError("Account does not belong to this program")
            res.append(cls.decode(info.account.data))
        return res

    @classmethod
    def decode(cls, data: bytes) -> "PerpMarket":
        if data[:ACCOUNT_DISCRIMINATOR_SIZE] != cls.discriminator:
            raise AccountInvalidDiscriminator(
                "The discriminator for this account is invalid"
            )
        dec = PerpMarket.layout.parse(data[ACCOUNT_DISCRIMINATOR_SIZE:])
        return cls(
            pubkey=dec.pubkey,
            amm=types.amm.AMM.from_decoded(dec.amm),
            pnl_pool=types.pool_balance.PoolBalance.from_decoded(dec.pnl_pool),
            name=dec.name,
            expiry_price=dec.expiry_price,
            number_of_users=dec.number_of_users,
            imf_factor=dec.imf_factor,
            unrealized_pnl_imf_factor=dec.unrealized_pnl_imf_factor,
            unrealized_pnl_max_imbalance=dec.unrealized_pnl_max_imbalance,
            liquidator_fee=dec.liquidator_fee,
            if_liquidation_fee=dec.if_liquidation_fee,
            insurance_claim=types.insurance_claim.InsuranceClaim.from_decoded(
                dec.insurance_claim
            ),
            expiry_ts=dec.expiry_ts,
            next_fill_record_id=dec.next_fill_record_id,
            next_funding_rate_record_id=dec.next_funding_rate_record_id,
            next_curve_record_id=dec.next_curve_record_id,
            margin_ratio_initial=dec.margin_ratio_initial,
            margin_ratio_maintenance=dec.margin_ratio_maintenance,
            unrealized_pnl_initial_asset_weight=dec.unrealized_pnl_initial_asset_weight,
            unrealized_pnl_maintenance_asset_weight=dec.unrealized_pnl_maintenance_asset_weight,
            market_index=dec.market_index,
            status=types.market_status.from_decoded(dec.status),
            contract_type=types.contract_type.from_decoded(dec.contract_type),
            contract_tier=types.contract_tier.from_decoded(dec.contract_tier),
            padding=dec.padding,
        )

    def to_json(self) -> PerpMarketJSON:
        return {
            "pubkey": str(self.pubkey),
            "amm": self.amm.to_json(),
            "pnl_pool": self.pnl_pool.to_json(),
            "name": self.name,
            "expiry_price": self.expiry_price,
            "number_of_users": self.number_of_users,
            "imf_factor": self.imf_factor,
            "unrealized_pnl_imf_factor": self.unrealized_pnl_imf_factor,
            "unrealized_pnl_max_imbalance": self.unrealized_pnl_max_imbalance,
            "liquidator_fee": self.liquidator_fee,
            "if_liquidation_fee": self.if_liquidation_fee,
            "insurance_claim": self.insurance_claim.to_json(),
            "expiry_ts": self.expiry_ts,
            "next_fill_record_id": self.next_fill_record_id,
            "next_funding_rate_record_id": self.next_funding_rate_record_id,
            "next_curve_record_id": self.next_curve_record_id,
            "margin_ratio_initial": self.margin_ratio_initial,
            "margin_ratio_maintenance": self.margin_ratio_maintenance,
            "unrealized_pnl_initial_asset_weight": self.unrealized_pnl_initial_asset_weight,
            "unrealized_pnl_maintenance_asset_weight": self.unrealized_pnl_maintenance_asset_weight,
            "market_index": self.market_index,
            "status": self.status.to_json(),
            "contract_type": self.contract_type.to_json(),
            "contract_tier": self.contract_tier.to_json(),
            "padding": self.padding,
        }

    @classmethod
    def from_json(cls, obj: PerpMarketJSON) -> "PerpMarket":
        return cls(
            pubkey=PublicKey(obj["pubkey"]),
            amm=types.amm.AMM.from_json(obj["amm"]),
            pnl_pool=types.pool_balance.PoolBalance.from_json(obj["pnl_pool"]),
            name=obj["name"],
            expiry_price=obj["expiry_price"],
            number_of_users=obj["number_of_users"],
            imf_factor=obj["imf_factor"],
            unrealized_pnl_imf_factor=obj["unrealized_pnl_imf_factor"],
            unrealized_pnl_max_imbalance=obj["unrealized_pnl_max_imbalance"],
            liquidator_fee=obj["liquidator_fee"],
            if_liquidation_fee=obj["if_liquidation_fee"],
            insurance_claim=types.insurance_claim.InsuranceClaim.from_json(
                obj["insurance_claim"]
            ),
            expiry_ts=obj["expiry_ts"],
            next_fill_record_id=obj["next_fill_record_id"],
            next_funding_rate_record_id=obj["next_funding_rate_record_id"],
            next_curve_record_id=obj["next_curve_record_id"],
            margin_ratio_initial=obj["margin_ratio_initial"],
            margin_ratio_maintenance=obj["margin_ratio_maintenance"],
            unrealized_pnl_initial_asset_weight=obj[
                "unrealized_pnl_initial_asset_weight"
            ],
            unrealized_pnl_maintenance_asset_weight=obj[
                "unrealized_pnl_maintenance_asset_weight"
            ],
            market_index=obj["market_index"],
            status=types.market_status.from_json(obj["status"]),
            contract_type=types.contract_type.from_json(obj["contract_type"]),
            contract_tier=types.contract_tier.from_json(obj["contract_tier"]),
            padding=obj["padding"],
        )
