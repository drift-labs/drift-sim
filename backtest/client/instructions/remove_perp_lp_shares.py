from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class RemovePerpLpSharesArgs(typing.TypedDict):
    shares_to_burn: int
    market_index: int


layout = borsh.CStruct("shares_to_burn" / borsh.U64, "market_index" / borsh.U16)


class RemovePerpLpSharesAccounts(typing.TypedDict):
    state: PublicKey
    user: PublicKey
    authority: PublicKey


def remove_perp_lp_shares(
    args: RemovePerpLpSharesArgs,
    accounts: RemovePerpLpSharesAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["state"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["user"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["authority"], is_signer=True, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\xd5Y\xd9\x12\xa075\x8d"
    encoded_args = layout.build(
        {
            "shares_to_burn": args["shares_to_burn"],
            "market_index": args["market_index"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
