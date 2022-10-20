from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class UpdateSpotMarketRevenueSettlePeriodArgs(typing.TypedDict):
    revenue_settle_period: int


layout = borsh.CStruct("revenue_settle_period" / borsh.I64)


class UpdateSpotMarketRevenueSettlePeriodAccounts(typing.TypedDict):
    admin: PublicKey
    state: PublicKey
    spot_market: PublicKey


def update_spot_market_revenue_settle_period(
    args: UpdateSpotMarketRevenueSettlePeriodArgs,
    accounts: UpdateSpotMarketRevenueSettlePeriodAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["admin"], is_signer=True, is_writable=False),
        AccountMeta(pubkey=accounts["state"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["spot_market"], is_signer=False, is_writable=True),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"Q\\~)\xfa\xe1\x9c\xdb"
    encoded_args = layout.build(
        {
            "revenue_settle_period": args["revenue_settle_period"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
