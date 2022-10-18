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


class SpotMarketJSON(typing.TypedDict):
    pubkey: str
    oracle: str
    mint: str
    vault: str
    historical_oracle_data: types.historical_oracle_data.HistoricalOracleDataJSON
    historical_index_data: types.historical_index_data.HistoricalIndexDataJSON
    revenue_pool: types.pool_balance.PoolBalanceJSON
    spot_fee_pool: types.pool_balance.PoolBalanceJSON
    insurance_fund: types.insurance_fund.InsuranceFundJSON
    initial_asset_weight: int
    maintenance_asset_weight: int
    initial_liability_weight: int
    maintenance_liability_weight: int
    imf_factor: int
    liquidator_fee: int
    if_liquidation_fee: int
    withdraw_guard_threshold: int
    total_spot_fee: int
    deposit_balance: int
    borrow_balance: int
    max_token_deposits: int
    deposit_token_twap: int
    borrow_token_twap: int
    utilization_twap: int
    cumulative_deposit_interest: int
    cumulative_borrow_interest: int
    last_interest_ts: int
    last_twap_ts: int
    expiry_ts: int
    order_step_size: int
    order_tick_size: int
    min_order_size: int
    max_position_size: int
    next_fill_record_id: int
    optimal_utilization: int
    optimal_borrow_rate: int
    max_borrow_rate: int
    market_index: int
    decimals: int
    oracle_source: types.oracle_source.OracleSourceJSON
    status: types.market_status.MarketStatusJSON
    asset_tier: types.asset_tier.AssetTierJSON
    padding: list[int]


@dataclass
class SpotMarket:
    discriminator: typing.ClassVar = b"d\xb1\x08k\xa8AA'"
    layout: typing.ClassVar = borsh.CStruct(
        "pubkey" / BorshPubkey,
        "oracle" / BorshPubkey,
        "mint" / BorshPubkey,
        "vault" / BorshPubkey,
        "historical_oracle_data"
        / types.historical_oracle_data.HistoricalOracleData.layout,
        "historical_index_data"
        / types.historical_index_data.HistoricalIndexData.layout,
        "revenue_pool" / types.pool_balance.PoolBalance.layout,
        "spot_fee_pool" / types.pool_balance.PoolBalance.layout,
        "insurance_fund" / types.insurance_fund.InsuranceFund.layout,
        "initial_asset_weight" / borsh.U128,
        "maintenance_asset_weight" / borsh.U128,
        "initial_liability_weight" / borsh.U128,
        "maintenance_liability_weight" / borsh.U128,
        "imf_factor" / borsh.U128,
        "liquidator_fee" / borsh.U128,
        "if_liquidation_fee" / borsh.U128,
        "withdraw_guard_threshold" / borsh.U128,
        "total_spot_fee" / borsh.U128,
        "deposit_balance" / borsh.U128,
        "borrow_balance" / borsh.U128,
        "max_token_deposits" / borsh.U128,
        "deposit_token_twap" / borsh.U128,
        "borrow_token_twap" / borsh.U128,
        "utilization_twap" / borsh.U128,
        "cumulative_deposit_interest" / borsh.U128,
        "cumulative_borrow_interest" / borsh.U128,
        "last_interest_ts" / borsh.U64,
        "last_twap_ts" / borsh.U64,
        "expiry_ts" / borsh.I64,
        "order_step_size" / borsh.U64,
        "order_tick_size" / borsh.U64,
        "min_order_size" / borsh.U64,
        "max_position_size" / borsh.U64,
        "next_fill_record_id" / borsh.U64,
        "optimal_utilization" / borsh.U32,
        "optimal_borrow_rate" / borsh.U32,
        "max_borrow_rate" / borsh.U32,
        "market_index" / borsh.U16,
        "decimals" / borsh.U8,
        "oracle_source" / types.oracle_source.layout,
        "status" / types.market_status.layout,
        "asset_tier" / types.asset_tier.layout,
        "padding" / borsh.U8[6],
    )
    pubkey: PublicKey
    oracle: PublicKey
    mint: PublicKey
    vault: PublicKey
    historical_oracle_data: types.historical_oracle_data.HistoricalOracleData
    historical_index_data: types.historical_index_data.HistoricalIndexData
    revenue_pool: types.pool_balance.PoolBalance
    spot_fee_pool: types.pool_balance.PoolBalance
    insurance_fund: types.insurance_fund.InsuranceFund
    initial_asset_weight: int
    maintenance_asset_weight: int
    initial_liability_weight: int
    maintenance_liability_weight: int
    imf_factor: int
    liquidator_fee: int
    if_liquidation_fee: int
    withdraw_guard_threshold: int
    total_spot_fee: int
    deposit_balance: int
    borrow_balance: int
    max_token_deposits: int
    deposit_token_twap: int
    borrow_token_twap: int
    utilization_twap: int
    cumulative_deposit_interest: int
    cumulative_borrow_interest: int
    last_interest_ts: int
    last_twap_ts: int
    expiry_ts: int
    order_step_size: int
    order_tick_size: int
    min_order_size: int
    max_position_size: int
    next_fill_record_id: int
    optimal_utilization: int
    optimal_borrow_rate: int
    max_borrow_rate: int
    market_index: int
    decimals: int
    oracle_source: types.oracle_source.OracleSourceKind
    status: types.market_status.MarketStatusKind
    asset_tier: types.asset_tier.AssetTierKind
    padding: list[int]

    @classmethod
    async def fetch(
        cls,
        conn: AsyncClient,
        address: PublicKey,
        commitment: typing.Optional[Commitment] = None,
        program_id: PublicKey = PROGRAM_ID,
    ) -> typing.Optional["SpotMarket"]:
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
    ) -> typing.List[typing.Optional["SpotMarket"]]:
        infos = await get_multiple_accounts(conn, addresses, commitment=commitment)
        res: typing.List[typing.Optional["SpotMarket"]] = []
        for info in infos:
            if info is None:
                res.append(None)
                continue
            if info.account.owner != program_id:
                raise ValueError("Account does not belong to this program")
            res.append(cls.decode(info.account.data))
        return res

    @classmethod
    def decode(cls, data: bytes) -> "SpotMarket":
        if data[:ACCOUNT_DISCRIMINATOR_SIZE] != cls.discriminator:
            raise AccountInvalidDiscriminator(
                "The discriminator for this account is invalid"
            )
        dec = SpotMarket.layout.parse(data[ACCOUNT_DISCRIMINATOR_SIZE:])
        return cls(
            pubkey=dec.pubkey,
            oracle=dec.oracle,
            mint=dec.mint,
            vault=dec.vault,
            historical_oracle_data=types.historical_oracle_data.HistoricalOracleData.from_decoded(
                dec.historical_oracle_data
            ),
            historical_index_data=types.historical_index_data.HistoricalIndexData.from_decoded(
                dec.historical_index_data
            ),
            revenue_pool=types.pool_balance.PoolBalance.from_decoded(dec.revenue_pool),
            spot_fee_pool=types.pool_balance.PoolBalance.from_decoded(
                dec.spot_fee_pool
            ),
            insurance_fund=types.insurance_fund.InsuranceFund.from_decoded(
                dec.insurance_fund
            ),
            initial_asset_weight=dec.initial_asset_weight,
            maintenance_asset_weight=dec.maintenance_asset_weight,
            initial_liability_weight=dec.initial_liability_weight,
            maintenance_liability_weight=dec.maintenance_liability_weight,
            imf_factor=dec.imf_factor,
            liquidator_fee=dec.liquidator_fee,
            if_liquidation_fee=dec.if_liquidation_fee,
            withdraw_guard_threshold=dec.withdraw_guard_threshold,
            total_spot_fee=dec.total_spot_fee,
            deposit_balance=dec.deposit_balance,
            borrow_balance=dec.borrow_balance,
            max_token_deposits=dec.max_token_deposits,
            deposit_token_twap=dec.deposit_token_twap,
            borrow_token_twap=dec.borrow_token_twap,
            utilization_twap=dec.utilization_twap,
            cumulative_deposit_interest=dec.cumulative_deposit_interest,
            cumulative_borrow_interest=dec.cumulative_borrow_interest,
            last_interest_ts=dec.last_interest_ts,
            last_twap_ts=dec.last_twap_ts,
            expiry_ts=dec.expiry_ts,
            order_step_size=dec.order_step_size,
            order_tick_size=dec.order_tick_size,
            min_order_size=dec.min_order_size,
            max_position_size=dec.max_position_size,
            next_fill_record_id=dec.next_fill_record_id,
            optimal_utilization=dec.optimal_utilization,
            optimal_borrow_rate=dec.optimal_borrow_rate,
            max_borrow_rate=dec.max_borrow_rate,
            market_index=dec.market_index,
            decimals=dec.decimals,
            oracle_source=types.oracle_source.from_decoded(dec.oracle_source),
            status=types.market_status.from_decoded(dec.status),
            asset_tier=types.asset_tier.from_decoded(dec.asset_tier),
            padding=dec.padding,
        )

    def to_json(self) -> SpotMarketJSON:
        return {
            "pubkey": str(self.pubkey),
            "oracle": str(self.oracle),
            "mint": str(self.mint),
            "vault": str(self.vault),
            "historical_oracle_data": self.historical_oracle_data.to_json(),
            "historical_index_data": self.historical_index_data.to_json(),
            "revenue_pool": self.revenue_pool.to_json(),
            "spot_fee_pool": self.spot_fee_pool.to_json(),
            "insurance_fund": self.insurance_fund.to_json(),
            "initial_asset_weight": self.initial_asset_weight,
            "maintenance_asset_weight": self.maintenance_asset_weight,
            "initial_liability_weight": self.initial_liability_weight,
            "maintenance_liability_weight": self.maintenance_liability_weight,
            "imf_factor": self.imf_factor,
            "liquidator_fee": self.liquidator_fee,
            "if_liquidation_fee": self.if_liquidation_fee,
            "withdraw_guard_threshold": self.withdraw_guard_threshold,
            "total_spot_fee": self.total_spot_fee,
            "deposit_balance": self.deposit_balance,
            "borrow_balance": self.borrow_balance,
            "max_token_deposits": self.max_token_deposits,
            "deposit_token_twap": self.deposit_token_twap,
            "borrow_token_twap": self.borrow_token_twap,
            "utilization_twap": self.utilization_twap,
            "cumulative_deposit_interest": self.cumulative_deposit_interest,
            "cumulative_borrow_interest": self.cumulative_borrow_interest,
            "last_interest_ts": self.last_interest_ts,
            "last_twap_ts": self.last_twap_ts,
            "expiry_ts": self.expiry_ts,
            "order_step_size": self.order_step_size,
            "order_tick_size": self.order_tick_size,
            "min_order_size": self.min_order_size,
            "max_position_size": self.max_position_size,
            "next_fill_record_id": self.next_fill_record_id,
            "optimal_utilization": self.optimal_utilization,
            "optimal_borrow_rate": self.optimal_borrow_rate,
            "max_borrow_rate": self.max_borrow_rate,
            "market_index": self.market_index,
            "decimals": self.decimals,
            "oracle_source": self.oracle_source.to_json(),
            "status": self.status.to_json(),
            "asset_tier": self.asset_tier.to_json(),
            "padding": self.padding,
        }

    @classmethod
    def from_json(cls, obj: SpotMarketJSON) -> "SpotMarket":
        return cls(
            pubkey=PublicKey(obj["pubkey"]),
            oracle=PublicKey(obj["oracle"]),
            mint=PublicKey(obj["mint"]),
            vault=PublicKey(obj["vault"]),
            historical_oracle_data=types.historical_oracle_data.HistoricalOracleData.from_json(
                obj["historical_oracle_data"]
            ),
            historical_index_data=types.historical_index_data.HistoricalIndexData.from_json(
                obj["historical_index_data"]
            ),
            revenue_pool=types.pool_balance.PoolBalance.from_json(obj["revenue_pool"]),
            spot_fee_pool=types.pool_balance.PoolBalance.from_json(
                obj["spot_fee_pool"]
            ),
            insurance_fund=types.insurance_fund.InsuranceFund.from_json(
                obj["insurance_fund"]
            ),
            initial_asset_weight=obj["initial_asset_weight"],
            maintenance_asset_weight=obj["maintenance_asset_weight"],
            initial_liability_weight=obj["initial_liability_weight"],
            maintenance_liability_weight=obj["maintenance_liability_weight"],
            imf_factor=obj["imf_factor"],
            liquidator_fee=obj["liquidator_fee"],
            if_liquidation_fee=obj["if_liquidation_fee"],
            withdraw_guard_threshold=obj["withdraw_guard_threshold"],
            total_spot_fee=obj["total_spot_fee"],
            deposit_balance=obj["deposit_balance"],
            borrow_balance=obj["borrow_balance"],
            max_token_deposits=obj["max_token_deposits"],
            deposit_token_twap=obj["deposit_token_twap"],
            borrow_token_twap=obj["borrow_token_twap"],
            utilization_twap=obj["utilization_twap"],
            cumulative_deposit_interest=obj["cumulative_deposit_interest"],
            cumulative_borrow_interest=obj["cumulative_borrow_interest"],
            last_interest_ts=obj["last_interest_ts"],
            last_twap_ts=obj["last_twap_ts"],
            expiry_ts=obj["expiry_ts"],
            order_step_size=obj["order_step_size"],
            order_tick_size=obj["order_tick_size"],
            min_order_size=obj["min_order_size"],
            max_position_size=obj["max_position_size"],
            next_fill_record_id=obj["next_fill_record_id"],
            optimal_utilization=obj["optimal_utilization"],
            optimal_borrow_rate=obj["optimal_borrow_rate"],
            max_borrow_rate=obj["max_borrow_rate"],
            market_index=obj["market_index"],
            decimals=obj["decimals"],
            oracle_source=types.oracle_source.from_json(obj["oracle_source"]),
            status=types.market_status.from_json(obj["status"]),
            asset_tier=types.asset_tier.from_json(obj["asset_tier"]),
            padding=obj["padding"],
        )
