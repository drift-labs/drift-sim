from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class UpdatePerpMarketMinOrderSizeArgs(typing.TypedDict):
    order_size: int


layout = borsh.CStruct("order_size" / borsh.U64)


class UpdatePerpMarketMinOrderSizeAccounts(typing.TypedDict):
    admin: PublicKey
    state: PublicKey
    perp_market: PublicKey


def update_perp_market_min_order_size(
    args: UpdatePerpMarketMinOrderSizeArgs,
    accounts: UpdatePerpMarketMinOrderSizeAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["admin"], is_signer=True, is_writable=False),
        AccountMeta(pubkey=accounts["state"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["perp_market"], is_signer=False, is_writable=True),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\xe2J\x05Yl\xdf.\x8d"
    encoded_args = layout.build(
        {
            "order_size": args["order_size"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
