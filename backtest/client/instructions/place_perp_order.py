from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from .. import types
from ..program_id import PROGRAM_ID


class PlacePerpOrderArgs(typing.TypedDict):
    params: types.order_params.OrderParams


layout = borsh.CStruct("params" / types.order_params.OrderParams.layout)


class PlacePerpOrderAccounts(typing.TypedDict):
    state: PublicKey
    user: PublicKey
    authority: PublicKey


def place_perp_order(
    args: PlacePerpOrderArgs,
    accounts: PlacePerpOrderAccounts,
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
    identifier = b"E\xa1]\xcax~L\xb9"
    encoded_args = layout.build(
        {
            "params": args["params"].to_encodable(),
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)