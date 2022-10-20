from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class UpdateAmmJitIntensityArgs(typing.TypedDict):
    amm_jit_intensity: int


layout = borsh.CStruct("amm_jit_intensity" / borsh.U8)


class UpdateAmmJitIntensityAccounts(typing.TypedDict):
    admin: PublicKey
    state: PublicKey
    perp_market: PublicKey


def update_amm_jit_intensity(
    args: UpdateAmmJitIntensityArgs,
    accounts: UpdateAmmJitIntensityAccounts,
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
    identifier = b"\xb5\xbf5m\xa6\xf97\x8e"
    encoded_args = layout.build(
        {
            "amm_jit_intensity": args["amm_jit_intensity"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
