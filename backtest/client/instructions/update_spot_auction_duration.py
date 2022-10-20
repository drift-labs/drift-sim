from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class UpdateSpotAuctionDurationArgs(typing.TypedDict):
    default_spot_auction_duration: int


layout = borsh.CStruct("default_spot_auction_duration" / borsh.U8)


class UpdateSpotAuctionDurationAccounts(typing.TypedDict):
    admin: PublicKey
    state: PublicKey


def update_spot_auction_duration(
    args: UpdateSpotAuctionDurationArgs,
    accounts: UpdateSpotAuctionDurationAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["admin"], is_signer=True, is_writable=False),
        AccountMeta(pubkey=accounts["state"], is_signer=False, is_writable=True),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\xb6\xb2\xcbH\xbb\x8f\x9dk"
    encoded_args = layout.build(
        {
            "default_spot_auction_duration": args["default_spot_auction_duration"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
