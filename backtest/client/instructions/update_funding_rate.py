from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class UpdateFundingRateArgs(typing.TypedDict):
    market_index: int


layout = borsh.CStruct("market_index" / borsh.U16)


class UpdateFundingRateAccounts(typing.TypedDict):
    state: PublicKey
    perp_market: PublicKey
    oracle: PublicKey


def update_funding_rate(
    args: UpdateFundingRateArgs,
    accounts: UpdateFundingRateAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["state"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["perp_market"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["oracle"], is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\xc9\xb2t\xd4\xa6\x90H\xee"
    encoded_args = layout.build(
        {
            "market_index": args["market_index"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
