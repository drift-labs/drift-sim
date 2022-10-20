from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from .. import types
from ..program_id import PROGRAM_ID


class InitializeSpotMarketArgs(typing.TypedDict):
    optimal_utilization: int
    optimal_borrow_rate: int
    max_borrow_rate: int
    oracle_source: types.oracle_source.OracleSourceKind
    initial_asset_weight: int
    maintenance_asset_weight: int
    initial_liability_weight: int
    maintenance_liability_weight: int
    imf_factor: int
    liquidation_fee: int
    active_status: bool


layout = borsh.CStruct(
    "optimal_utilization" / borsh.U32,
    "optimal_borrow_rate" / borsh.U32,
    "max_borrow_rate" / borsh.U32,
    "oracle_source" / types.oracle_source.layout,
    "initial_asset_weight" / borsh.U128,
    "maintenance_asset_weight" / borsh.U128,
    "initial_liability_weight" / borsh.U128,
    "maintenance_liability_weight" / borsh.U128,
    "imf_factor" / borsh.U128,
    "liquidation_fee" / borsh.U128,
    "active_status" / borsh.Bool,
)


class InitializeSpotMarketAccounts(typing.TypedDict):
    spot_market: PublicKey
    spot_market_mint: PublicKey
    spot_market_vault: PublicKey
    insurance_fund_vault: PublicKey
    clearing_house_signer: PublicKey
    state: PublicKey
    oracle: PublicKey
    admin: PublicKey
    rent: PublicKey
    system_program: PublicKey
    token_program: PublicKey


def initialize_spot_market(
    args: InitializeSpotMarketArgs,
    accounts: InitializeSpotMarketAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["spot_market"], is_signer=False, is_writable=True),
        AccountMeta(
            pubkey=accounts["spot_market_mint"], is_signer=False, is_writable=False
        ),
        AccountMeta(
            pubkey=accounts["spot_market_vault"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["insurance_fund_vault"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["clearing_house_signer"], is_signer=False, is_writable=False
        ),
        AccountMeta(pubkey=accounts["state"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["oracle"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["admin"], is_signer=True, is_writable=True),
        AccountMeta(pubkey=accounts["rent"], is_signer=False, is_writable=False),
        AccountMeta(
            pubkey=accounts["system_program"], is_signer=False, is_writable=False
        ),
        AccountMeta(
            pubkey=accounts["token_program"], is_signer=False, is_writable=False
        ),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\xea\xc4\x80,^\x0f0\xc9"
    encoded_args = layout.build(
        {
            "optimal_utilization": args["optimal_utilization"],
            "optimal_borrow_rate": args["optimal_borrow_rate"],
            "max_borrow_rate": args["max_borrow_rate"],
            "oracle_source": args["oracle_source"].to_encodable(),
            "initial_asset_weight": args["initial_asset_weight"],
            "maintenance_asset_weight": args["maintenance_asset_weight"],
            "initial_liability_weight": args["initial_liability_weight"],
            "maintenance_liability_weight": args["maintenance_liability_weight"],
            "imf_factor": args["imf_factor"],
            "liquidation_fee": args["liquidation_fee"],
            "active_status": args["active_status"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
