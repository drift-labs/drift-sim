from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from .. import types
from ..program_id import PROGRAM_ID


class FillSpotOrderArgs(typing.TypedDict):
    order_id: typing.Optional[int]
    fulfillment_type: typing.Optional[
        types.spot_fulfillment_type.SpotFulfillmentTypeKind
    ]
    maker_order_id: typing.Optional[int]


layout = borsh.CStruct(
    "order_id" / borsh.Option(borsh.U32),
    "fulfillment_type" / borsh.Option(types.spot_fulfillment_type.layout),
    "maker_order_id" / borsh.Option(borsh.U32),
)


class FillSpotOrderAccounts(typing.TypedDict):
    state: PublicKey
    authority: PublicKey
    filler: PublicKey
    filler_stats: PublicKey
    user: PublicKey
    user_stats: PublicKey


def fill_spot_order(
    args: FillSpotOrderArgs,
    accounts: FillSpotOrderAccounts,
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
    identifier = b'\xd4\xce\x82\xad\x15"\xc7('
    encoded_args = layout.build(
        {
            "order_id": args["order_id"],
            "fulfillment_type": (
                None
                if args["fulfillment_type"] is None
                else args["fulfillment_type"].to_encodable()
            ),
            "maker_order_id": args["maker_order_id"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
