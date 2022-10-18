from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class UpdateInsuranceFundUnstakingPeriodArgs(typing.TypedDict):
    insurance_fund_unstaking_period: int


layout = borsh.CStruct("insurance_fund_unstaking_period" / borsh.I64)


class UpdateInsuranceFundUnstakingPeriodAccounts(typing.TypedDict):
    admin: PublicKey
    state: PublicKey
    spot_market: PublicKey


def update_insurance_fund_unstaking_period(
    args: UpdateInsuranceFundUnstakingPeriodArgs,
    accounts: UpdateInsuranceFundUnstakingPeriodAccounts,
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
    identifier = b",E+\xe2\xcc\xdf\xca4"
    encoded_args = layout.build(
        {
            "insurance_fund_unstaking_period": args["insurance_fund_unstaking_period"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
