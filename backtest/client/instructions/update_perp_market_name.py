from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class UpdatePerpMarketNameArgs(typing.TypedDict):
    name: list[int]


layout = borsh.CStruct("name" / borsh.U8[32])


class UpdatePerpMarketNameAccounts(typing.TypedDict):
    admin: PublicKey
    state: PublicKey
    perp_market: PublicKey


def update_perp_market_name(
    args: UpdatePerpMarketNameArgs,
    accounts: UpdatePerpMarketNameAccounts,
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
    identifier = b"\xd3\x1f\x15\xd2@lB\xc9"
    encoded_args = layout.build(
        {
            "name": args["name"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
