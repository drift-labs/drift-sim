from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
from anchorpy.borsh_extension import BorshPubkey
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class UpdateAdminArgs(typing.TypedDict):
    admin: PublicKey


layout = borsh.CStruct("admin" / BorshPubkey)


class UpdateAdminAccounts(typing.TypedDict):
    admin: PublicKey
    state: PublicKey


def update_admin(
    args: UpdateAdminArgs,
    accounts: UpdateAdminAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["admin"], is_signer=True, is_writable=False),
        AccountMeta(pubkey=accounts["state"], is_signer=False, is_writable=True),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\xa1\xb0(\xd5<\xb8\xb3\xe4"
    encoded_args = layout.build(
        {
            "admin": args["admin"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
