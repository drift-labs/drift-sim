from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class UpdatePerpMarketMaxSlippageRatioArgs(typing.TypedDict):
    max_slippage_ratio: int


layout = borsh.CStruct("max_slippage_ratio" / borsh.U16)


class UpdatePerpMarketMaxSlippageRatioAccounts(typing.TypedDict):
    admin: PublicKey
    state: PublicKey
    perp_market: PublicKey


def update_perp_market_max_slippage_ratio(
    args: UpdatePerpMarketMaxSlippageRatioArgs,
    accounts: UpdatePerpMarketMaxSlippageRatioAccounts,
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
    identifier = b"\xeb%(\xc4F\x926\xc9"
    encoded_args = layout.build(
        {
            "max_slippage_ratio": args["max_slippage_ratio"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
