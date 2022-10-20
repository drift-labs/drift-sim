from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class TriggerOrderArgs(typing.TypedDict):
    order_id: int


layout = borsh.CStruct("order_id" / borsh.U32)


class TriggerOrderAccounts(typing.TypedDict):
    state: PublicKey
    authority: PublicKey
    filler: PublicKey
    user: PublicKey


def trigger_order(
    args: TriggerOrderArgs,
    accounts: TriggerOrderAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["state"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["authority"], is_signer=True, is_writable=False),
        AccountMeta(pubkey=accounts["filler"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["user"], is_signer=False, is_writable=True),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"?p3\xe9\xe8/\xf0\xc7"
    encoded_args = layout.build(
        {
            "order_id": args["order_id"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
