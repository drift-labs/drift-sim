from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class DepositArgs(typing.TypedDict):
    market_index: int
    amount: int
    reduce_only: bool


layout = borsh.CStruct(
    "market_index" / borsh.U16, "amount" / borsh.U64, "reduce_only" / borsh.Bool
)


class DepositAccounts(typing.TypedDict):
    state: PublicKey
    user: PublicKey
    user_stats: PublicKey
    authority: PublicKey
    spot_market_vault: PublicKey
    user_token_account: PublicKey
    token_program: PublicKey


def deposit(
    args: DepositArgs,
    accounts: DepositAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["state"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["user"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["user_stats"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["authority"], is_signer=True, is_writable=False),
        AccountMeta(
            pubkey=accounts["spot_market_vault"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["user_token_account"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["token_program"], is_signer=False, is_writable=False
        ),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\xf2#\xc6\x89R\xe1\xf2\xb6"
    encoded_args = layout.build(
        {
            "market_index": args["market_index"],
            "amount": args["amount"],
            "reduce_only": args["reduce_only"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
