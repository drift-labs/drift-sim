from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class UpdateAmmsArgs(typing.TypedDict):
    market_indexes: list[int]


layout = borsh.CStruct("market_indexes" / borsh.U16[5])


class UpdateAmmsAccounts(typing.TypedDict):
    state: PublicKey
    authority: PublicKey


def update_amms(
    args: UpdateAmmsArgs,
    accounts: UpdateAmmsAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["state"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["authority"], is_signer=True, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\xc9j\xd9\xfd\x04\xaf\xe4a"
    encoded_args = layout.build(
        {
            "market_indexes": args["market_indexes"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
