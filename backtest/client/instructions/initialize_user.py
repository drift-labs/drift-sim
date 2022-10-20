from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class InitializeUserArgs(typing.TypedDict):
    sub_account_id: int
    name: list[int]


layout = borsh.CStruct("sub_account_id" / borsh.U8, "name" / borsh.U8[32])


class InitializeUserAccounts(typing.TypedDict):
    user: PublicKey
    user_stats: PublicKey
    state: PublicKey
    authority: PublicKey
    payer: PublicKey
    rent: PublicKey
    system_program: PublicKey


def initialize_user(
    args: InitializeUserArgs,
    accounts: InitializeUserAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["user"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["user_stats"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["state"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["authority"], is_signer=True, is_writable=False),
        AccountMeta(pubkey=accounts["payer"], is_signer=True, is_writable=True),
        AccountMeta(pubkey=accounts["rent"], is_signer=False, is_writable=False),
        AccountMeta(
            pubkey=accounts["system_program"], is_signer=False, is_writable=False
        ),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"o\x11\xb9\xfa<z&\xfe"
    encoded_args = layout.build(
        {
            "sub_account_id": args["sub_account_id"],
            "name": args["name"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
