from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from .. import types
from ..program_id import PROGRAM_ID


class UpdateSpotMarketAssetTierArgs(typing.TypedDict):
    asset_tier: types.asset_tier.AssetTierKind


layout = borsh.CStruct("asset_tier" / types.asset_tier.layout)


class UpdateSpotMarketAssetTierAccounts(typing.TypedDict):
    admin: PublicKey
    state: PublicKey
    spot_market: PublicKey


def update_spot_market_asset_tier(
    args: UpdateSpotMarketAssetTierArgs,
    accounts: UpdateSpotMarketAssetTierAccounts,
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
    identifier = b"\xfd\xd1\xe7\x0e\xf2\xd0\xf3\x82"
    encoded_args = layout.build(
        {
            "asset_tier": args["asset_tier"].to_encodable(),
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
