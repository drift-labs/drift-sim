from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class SettleRevenueToInsuranceFundArgs(typing.TypedDict):
    spot_market_index: int


layout = borsh.CStruct("spot_market_index" / borsh.U16)


class SettleRevenueToInsuranceFundAccounts(typing.TypedDict):
    state: PublicKey
    spot_market: PublicKey
    spot_market_vault: PublicKey
    clearing_house_signer: PublicKey
    insurance_fund_vault: PublicKey
    token_program: PublicKey


def settle_revenue_to_insurance_fund(
    args: SettleRevenueToInsuranceFundArgs,
    accounts: SettleRevenueToInsuranceFundAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["state"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["spot_market"], is_signer=False, is_writable=False),
        AccountMeta(
            pubkey=accounts["spot_market_vault"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["clearing_house_signer"], is_signer=False, is_writable=False
        ),
        AccountMeta(
            pubkey=accounts["insurance_fund_vault"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["token_program"], is_signer=False, is_writable=False
        ),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\xc8x]\x88E&\xc7\x9f"
    encoded_args = layout.build(
        {
            "spot_market_index": args["spot_market_index"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
