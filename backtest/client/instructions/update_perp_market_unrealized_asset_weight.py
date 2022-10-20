from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class UpdatePerpMarketUnrealizedAssetWeightArgs(typing.TypedDict):
    unrealized_initial_asset_weight: int
    unrealized_maintenance_asset_weight: int


layout = borsh.CStruct(
    "unrealized_initial_asset_weight" / borsh.U32,
    "unrealized_maintenance_asset_weight" / borsh.U32,
)


class UpdatePerpMarketUnrealizedAssetWeightAccounts(typing.TypedDict):
    admin: PublicKey
    state: PublicKey
    perp_market: PublicKey


def update_perp_market_unrealized_asset_weight(
    args: UpdatePerpMarketUnrealizedAssetWeightArgs,
    accounts: UpdatePerpMarketUnrealizedAssetWeightAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["admin"], is_signer=True, is_writable=False),
        AccountMeta(pubkey=accounts["state"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["perp_market"], is_signer=False, is_writable=True),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\x87\x84\xcd\xa5m\x96\xa6j"
    encoded_args = layout.build(
        {
            "unrealized_initial_asset_weight": args["unrealized_initial_asset_weight"],
            "unrealized_maintenance_asset_weight": args[
                "unrealized_maintenance_asset_weight"
            ],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
