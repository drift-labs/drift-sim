from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
from ..program_id import PROGRAM_ID


class ResetPerpMarketAmmOracleTwapAccounts(typing.TypedDict):
    state: PublicKey
    perp_market: PublicKey
    oracle: PublicKey
    admin: PublicKey


def reset_perp_market_amm_oracle_twap(
    accounts: ResetPerpMarketAmmOracleTwapAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["state"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["perp_market"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["oracle"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["admin"], is_signer=True, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\x7f\n7\xa4{\xe2/\x18"
    encoded_args = b""
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
