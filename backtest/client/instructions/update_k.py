from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class UpdateKArgs(typing.TypedDict):
    sqrt_k: int


layout = borsh.CStruct("sqrt_k" / borsh.U128)


class UpdateKAccounts(typing.TypedDict):
    admin: PublicKey
    state: PublicKey
    perp_market: PublicKey
    oracle: PublicKey


def update_k(
    args: UpdateKArgs,
    accounts: UpdateKAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["admin"], is_signer=True, is_writable=False),
        AccountMeta(pubkey=accounts["state"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["perp_market"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["oracle"], is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"Hb\t\x8b\x81\xe5\xac8"
    encoded_args = layout.build(
        {
            "sqrt_k": args["sqrt_k"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
