from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class UpdateUserNameArgs(typing.TypedDict):
    sub_account_id: int
    name: list[int]


layout = borsh.CStruct("sub_account_id" / borsh.U8, "name" / borsh.U8[32])


class UpdateUserNameAccounts(typing.TypedDict):
    user: PublicKey
    authority: PublicKey


def update_user_name(
    args: UpdateUserNameArgs,
    accounts: UpdateUserNameAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["user"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["authority"], is_signer=True, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b'\x87\x19\xb98\xa55"\x88'
    encoded_args = layout.build(
        {
            "sub_account_id": args["sub_account_id"],
            "name": args["name"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
