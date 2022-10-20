from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class UpdatePerpMarketMaxImbalancesArgs(typing.TypedDict):
    unrealized_max_imbalance: int
    max_revenue_withdraw_per_period: int
    quote_max_insurance: int


layout = borsh.CStruct(
    "unrealized_max_imbalance" / borsh.U128,
    "max_revenue_withdraw_per_period" / borsh.U128,
    "quote_max_insurance" / borsh.U128,
)


class UpdatePerpMarketMaxImbalancesAccounts(typing.TypedDict):
    admin: PublicKey
    state: PublicKey
    perp_market: PublicKey


def update_perp_market_max_imbalances(
    args: UpdatePerpMarketMaxImbalancesArgs,
    accounts: UpdatePerpMarketMaxImbalancesAccounts,
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
    identifier = b"\x0f\xceI\x85<\x08VY"
    encoded_args = layout.build(
        {
            "unrealized_max_imbalance": args["unrealized_max_imbalance"],
            "max_revenue_withdraw_per_period": args["max_revenue_withdraw_per_period"],
            "quote_max_insurance": args["quote_max_insurance"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
