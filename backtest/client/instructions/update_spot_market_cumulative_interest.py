from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
from ..program_id import PROGRAM_ID


class UpdateSpotMarketCumulativeInterestAccounts(typing.TypedDict):
    state: PublicKey
    spot_market: PublicKey


def update_spot_market_cumulative_interest(
    accounts: UpdateSpotMarketCumulativeInterestAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["state"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["spot_market"], is_signer=False, is_writable=True),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"'\xa6\x8b\xf3\x9e\xa5\x9b\xe1"
    encoded_args = b""
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
