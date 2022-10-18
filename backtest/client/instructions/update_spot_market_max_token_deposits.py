from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class UpdateSpotMarketMaxTokenDepositsArgs(typing.TypedDict):
    max_token_deposits: int


layout = borsh.CStruct("max_token_deposits" / borsh.U128)


class UpdateSpotMarketMaxTokenDepositsAccounts(typing.TypedDict):
    admin: PublicKey
    state: PublicKey
    spot_market: PublicKey


def update_spot_market_max_token_deposits(
    args: UpdateSpotMarketMaxTokenDepositsArgs,
    accounts: UpdateSpotMarketMaxTokenDepositsAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["admin"], is_signer=True, is_writable=False),
        AccountMeta(pubkey=accounts["state"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["spot_market"], is_signer=False, is_writable=True),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"8\xbfO\x12\x1ayP\xd0"
    encoded_args = layout.build(
        {
            "max_token_deposits": args["max_token_deposits"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
