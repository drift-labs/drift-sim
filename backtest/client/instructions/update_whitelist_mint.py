from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
from anchorpy.borsh_extension import BorshPubkey
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class UpdateWhitelistMintArgs(typing.TypedDict):
    whitelist_mint: PublicKey


layout = borsh.CStruct("whitelist_mint" / BorshPubkey)


class UpdateWhitelistMintAccounts(typing.TypedDict):
    admin: PublicKey
    state: PublicKey


def update_whitelist_mint(
    args: UpdateWhitelistMintArgs,
    accounts: UpdateWhitelistMintAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["admin"], is_signer=True, is_writable=False),
        AccountMeta(pubkey=accounts["state"], is_signer=False, is_writable=True),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\xa1\x0f\xa2\x13\x94x\x90\x97"
    encoded_args = layout.build(
        {
            "whitelist_mint": args["whitelist_mint"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
