from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
from ..program_id import PROGRAM_ID


class UpdateUserQuoteAssetInsuranceStakeAccounts(typing.TypedDict):
    state: PublicKey
    spot_market: PublicKey
    insurance_fund_stake: PublicKey
    user_stats: PublicKey
    authority: PublicKey
    insurance_fund_vault: PublicKey


def update_user_quote_asset_insurance_stake(
    accounts: UpdateUserQuoteAssetInsuranceStakeAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["state"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["spot_market"], is_signer=False, is_writable=False),
        AccountMeta(
            pubkey=accounts["insurance_fund_stake"], is_signer=False, is_writable=True
        ),
        AccountMeta(pubkey=accounts["user_stats"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["authority"], is_signer=True, is_writable=False),
        AccountMeta(
            pubkey=accounts["insurance_fund_vault"], is_signer=False, is_writable=True
        ),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\xfbe\x9c\x07\x02?\x1e\x17"
    encoded_args = b""
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
