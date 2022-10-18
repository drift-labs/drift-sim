from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from .. import types
from ..program_id import PROGRAM_ID


class UpdateOracleGuardRailsArgs(typing.TypedDict):
    oracle_guard_rails: types.oracle_guard_rails.OracleGuardRails


layout = borsh.CStruct(
    "oracle_guard_rails" / types.oracle_guard_rails.OracleGuardRails.layout
)


class UpdateOracleGuardRailsAccounts(typing.TypedDict):
    admin: PublicKey
    state: PublicKey


def update_oracle_guard_rails(
    args: UpdateOracleGuardRailsArgs,
    accounts: UpdateOracleGuardRailsAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["admin"], is_signer=True, is_writable=False),
        AccountMeta(pubkey=accounts["state"], is_signer=False, is_writable=True),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\x83p\n; 6(\xa4"
    encoded_args = layout.build(
        {
            "oracle_guard_rails": args["oracle_guard_rails"].to_encodable(),
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
