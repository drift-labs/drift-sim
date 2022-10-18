from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from .. import types
from ..program_id import PROGRAM_ID


class PlaceSpotOrderArgs(typing.TypedDict):
    params: types.order_params.OrderParams


layout = borsh.CStruct("params" / types.order_params.OrderParams.layout)


class PlaceSpotOrderAccounts(typing.TypedDict):
    state: PublicKey
    user: PublicKey
    authority: PublicKey


def place_spot_order(
    args: PlaceSpotOrderArgs,
    accounts: PlaceSpotOrderAccounts,
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
    identifier = b"-OQ\xa0\xf8Z[\xdc"
    encoded_args = layout.build(
        {
            "params": args["params"].to_encodable(),
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
