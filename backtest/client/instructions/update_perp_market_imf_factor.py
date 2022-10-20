from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class UpdatePerpMarketImfFactorArgs(typing.TypedDict):
    imf_factor: int


layout = borsh.CStruct("imf_factor" / borsh.U128)


class UpdatePerpMarketImfFactorAccounts(typing.TypedDict):
    admin: PublicKey
    state: PublicKey
    perp_market: PublicKey


def update_perp_market_imf_factor(
    args: UpdatePerpMarketImfFactorArgs,
    accounts: UpdatePerpMarketImfFactorAccounts,
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
    identifier = b"\xcf\xc28\x84#CG\xf4"
    encoded_args = layout.build(
        {
            "imf_factor": args["imf_factor"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
