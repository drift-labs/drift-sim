from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class CancelOrderByUserIdArgs(typing.TypedDict):
    user_order_id: int


layout = borsh.CStruct("user_order_id" / borsh.U8)


class CancelOrderByUserIdAccounts(typing.TypedDict):
    state: PublicKey
    user: PublicKey
    authority: PublicKey


def cancel_order_by_user_id(
    args: CancelOrderByUserIdArgs,
    accounts: CancelOrderByUserIdAccounts,
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
    identifier = b"k\xd3\xfa\x85\x12%9d"
    encoded_args = layout.build(
        {
            "user_order_id": args["user_order_id"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
