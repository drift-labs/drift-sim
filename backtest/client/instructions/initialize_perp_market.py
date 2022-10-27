from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from .. import types
from ..program_id import PROGRAM_ID


class InitializePerpMarketArgs(typing.TypedDict):
    amm_base_asset_reserve: int
    amm_quote_asset_reserve: int
    amm_periodicity: int
    amm_peg_multiplier: int
    oracle_source: types.oracle_source.OracleSourceKind
    margin_ratio_initial: int
    margin_ratio_maintenance: int
    liquidation_fee: int
    active_status: bool
    name: list[int]


layout = borsh.CStruct(
    "amm_base_asset_reserve" / borsh.U128,
    "amm_quote_asset_reserve" / borsh.U128,
    "amm_periodicity" / borsh.I64,
    "amm_peg_multiplier" / borsh.U128,
    "oracle_source" / types.oracle_source.layout,
    "margin_ratio_initial" / borsh.U32,
    "margin_ratio_maintenance" / borsh.U32,
    "liquidation_fee" / borsh.U32,
    "active_status" / borsh.Bool,
    "name" / borsh.U8[32],
)


class InitializePerpMarketAccounts(typing.TypedDict):
    admin: PublicKey
    state: PublicKey
    perp_market: PublicKey
    oracle: PublicKey
    rent: PublicKey
    system_program: PublicKey


def initialize_perp_market(
    args: InitializePerpMarketArgs,
    accounts: InitializePerpMarketAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["admin"], is_signer=True, is_writable=True),
        AccountMeta(pubkey=accounts["state"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["perp_market"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["oracle"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["rent"], is_signer=False, is_writable=False),
        AccountMeta(
            pubkey=accounts["system_program"], is_signer=False, is_writable=False
        ),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\x84\t\xe5vuvu>"
    encoded_args = layout.build(
        {
            "amm_base_asset_reserve": args["amm_base_asset_reserve"],
            "amm_quote_asset_reserve": args["amm_quote_asset_reserve"],
            "amm_periodicity": args["amm_periodicity"],
            "amm_peg_multiplier": args["amm_peg_multiplier"],
            "oracle_source": args["oracle_source"].to_encodable(),
            "margin_ratio_initial": args["margin_ratio_initial"],
            "margin_ratio_maintenance": args["margin_ratio_maintenance"],
            "liquidation_fee": args["liquidation_fee"],
            "active_status": args["active_status"],
            "name": args["name"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
