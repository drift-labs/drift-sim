from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class UpdatePerpMarketMarginRatioArgs(typing.TypedDict):
    margin_ratio_initial: int
    margin_ratio_maintenance: int


layout = borsh.CStruct(
    "margin_ratio_initial" / borsh.U32, "margin_ratio_maintenance" / borsh.U32
)


class UpdatePerpMarketMarginRatioAccounts(typing.TypedDict):
    admin: PublicKey
    state: PublicKey
    perp_market: PublicKey


def update_perp_market_margin_ratio(
    args: UpdatePerpMarketMarginRatioArgs,
    accounts: UpdatePerpMarketMarginRatioAccounts,
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
    identifier = b"\x82\xadk-wi\x1aq"
    encoded_args = layout.build(
        {
            "margin_ratio_initial": args["margin_ratio_initial"],
            "margin_ratio_maintenance": args["margin_ratio_maintenance"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
