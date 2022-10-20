from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
from anchorpy.borsh_extension import BorshPubkey
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class UpdateDiscountMintArgs(typing.TypedDict):
    discount_mint: PublicKey


layout = borsh.CStruct("discount_mint" / BorshPubkey)


class UpdateDiscountMintAccounts(typing.TypedDict):
    admin: PublicKey
    state: PublicKey


def update_discount_mint(
    args: UpdateDiscountMintArgs,
    accounts: UpdateDiscountMintAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["admin"], is_signer=True, is_writable=False),
        AccountMeta(pubkey=accounts["state"], is_signer=False, is_writable=True),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b" \xfcz\xd3B\x1f/\xf1"
    encoded_args = layout.build(
        {
            "discount_mint": args["discount_mint"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
