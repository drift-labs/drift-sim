from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from .. import types
from ..program_id import PROGRAM_ID


class UpdateSpotMarketStatusArgs(typing.TypedDict):
    status: types.market_status.MarketStatusKind


layout = borsh.CStruct("status" / types.market_status.layout)


class UpdateSpotMarketStatusAccounts(typing.TypedDict):
    admin: PublicKey
    state: PublicKey
    spot_market: PublicKey


def update_spot_market_status(
    args: UpdateSpotMarketStatusArgs,
    accounts: UpdateSpotMarketStatusAccounts,
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
    identifier = b"N^\x10\xbc\xc1n\xe7\x1f"
    encoded_args = layout.build(
        {
            "status": args["status"].to_encodable(),
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
