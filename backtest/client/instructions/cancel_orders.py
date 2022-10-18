from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from .. import types
from ..program_id import PROGRAM_ID


class CancelOrdersArgs(typing.TypedDict):
    market_type: typing.Optional[types.market_type.MarketTypeKind]
    market_index: typing.Optional[int]
    direction: typing.Optional[types.position_direction.PositionDirectionKind]


layout = borsh.CStruct(
    "market_type" / borsh.Option(types.market_type.layout),
    "market_index" / borsh.Option(borsh.U16),
    "direction" / borsh.Option(types.position_direction.layout),
)


class CancelOrdersAccounts(typing.TypedDict):
    state: PublicKey
    user: PublicKey
    authority: PublicKey


def cancel_orders(
    args: CancelOrdersArgs,
    accounts: CancelOrdersAccounts,
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
    identifier = b"\xee\xe1_\x9e\xe3g\x08\xc2"
    encoded_args = layout.build(
        {
            "market_type": (
                None
                if args["market_type"] is None
                else args["market_type"].to_encodable()
            ),
            "market_index": args["market_index"],
            "direction": (
                None if args["direction"] is None else args["direction"].to_encodable()
            ),
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
