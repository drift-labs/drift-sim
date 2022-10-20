from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from .. import types
from ..program_id import PROGRAM_ID


class PlaceAndTakeArgs(typing.TypedDict):
    params: types.order_params.OrderParams
    maker_order_id: typing.Optional[int]


layout = borsh.CStruct(
    "params" / types.order_params.OrderParams.layout,
    "maker_order_id" / borsh.Option(borsh.U32),
)


class PlaceAndTakeAccounts(typing.TypedDict):
    state: PublicKey
    user: PublicKey
    user_stats: PublicKey
    authority: PublicKey


def place_and_take(
    args: PlaceAndTakeArgs,
    accounts: PlaceAndTakeAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["state"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["user"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["user_stats"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["authority"], is_signer=True, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"P\xfb\x17\xf1\x93\xed\x87\x92"
    encoded_args = layout.build(
        {
            "params": args["params"].to_encodable(),
            "maker_order_id": args["maker_order_id"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
