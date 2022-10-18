from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class UpdatePerpAuctionDurationArgs(typing.TypedDict):
    min_perp_auction_duration: int


layout = borsh.CStruct("min_perp_auction_duration" / borsh.U8)


class UpdatePerpAuctionDurationAccounts(typing.TypedDict):
    admin: PublicKey
    state: PublicKey


def update_perp_auction_duration(
    args: UpdatePerpAuctionDurationArgs,
    accounts: UpdatePerpAuctionDurationAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["admin"], is_signer=True, is_writable=False),
        AccountMeta(pubkey=accounts["state"], is_signer=False, is_writable=True),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"~n4\xae\x1e\xce\xd7Z"
    encoded_args = layout.build(
        {
            "min_perp_auction_duration": args["min_perp_auction_duration"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
