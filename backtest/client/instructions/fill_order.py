from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class FillOrderArgs(typing.TypedDict):
    order_id: typing.Optional[int]
    maker_order_id: typing.Optional[int]


layout = borsh.CStruct(
    "order_id" / borsh.Option(borsh.U32), "maker_order_id" / borsh.Option(borsh.U32)
)


class FillOrderAccounts(typing.TypedDict):
    state: PublicKey
    authority: PublicKey
    filler: PublicKey
    filler_stats: PublicKey
    user: PublicKey
    user_stats: PublicKey


def fill_order(
    args: FillOrderArgs,
    accounts: FillOrderAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["state"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["authority"], is_signer=True, is_writable=False),
        AccountMeta(pubkey=accounts["filler"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["filler_stats"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["user"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["user_stats"], is_signer=False, is_writable=True),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\xe8zs\x19\xc7\x8f\x88\xa2"
    encoded_args = layout.build(
        {
            "order_id": args["order_id"],
            "maker_order_id": args["maker_order_id"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
