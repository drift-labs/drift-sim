from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class UpdateSpotMarketMarginWeightsArgs(typing.TypedDict):
    initial_asset_weight: int
    maintenance_asset_weight: int
    initial_liability_weight: int
    maintenance_liability_weight: int
    imf_factor: int


layout = borsh.CStruct(
    "initial_asset_weight" / borsh.U128,
    "maintenance_asset_weight" / borsh.U128,
    "initial_liability_weight" / borsh.U128,
    "maintenance_liability_weight" / borsh.U128,
    "imf_factor" / borsh.U128,
)


class UpdateSpotMarketMarginWeightsAccounts(typing.TypedDict):
    admin: PublicKey
    state: PublicKey
    spot_market: PublicKey


def update_spot_market_margin_weights(
    args: UpdateSpotMarketMarginWeightsArgs,
    accounts: UpdateSpotMarketMarginWeightsAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["admin"], is_signer=True, is_writable=False),
        AccountMeta(pubkey=accounts["state"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["spot_market"], is_signer=False, is_writable=True),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"m!W\xc3\xff$\x06Q"
    encoded_args = layout.build(
        {
            "initial_asset_weight": args["initial_asset_weight"],
            "maintenance_asset_weight": args["maintenance_asset_weight"],
            "initial_liability_weight": args["initial_liability_weight"],
            "maintenance_liability_weight": args["maintenance_liability_weight"],
            "imf_factor": args["imf_factor"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
