from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class CancelOrderArgs(typing.TypedDict):
    order_id: typing.Optional[int]


layout = borsh.CStruct("order_id" / borsh.Option(borsh.U32))


class CancelOrderAccounts(typing.TypedDict):
    state: PublicKey
    user: PublicKey
    authority: PublicKey


def cancel_order(
    args: CancelOrderArgs,
    accounts: CancelOrderAccounts,
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
    identifier = b"_\x81\xed\xf0\x081\xdf\x84"
    encoded_args = layout.build(
        {
            "order_id": args["order_id"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
