from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class RequestRemoveInsuranceFundStakeArgs(typing.TypedDict):
    market_index: int
    amount: int


layout = borsh.CStruct("market_index" / borsh.U16, "amount" / borsh.U64)


class RequestRemoveInsuranceFundStakeAccounts(typing.TypedDict):
    spot_market: PublicKey
    insurance_fund_stake: PublicKey
    user_stats: PublicKey
    authority: PublicKey
    insurance_fund_vault: PublicKey


def request_remove_insurance_fund_stake(
    args: RequestRemoveInsuranceFundStakeArgs,
    accounts: RequestRemoveInsuranceFundStakeAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["spot_market"], is_signer=False, is_writable=False),
        AccountMeta(
            pubkey=accounts["insurance_fund_stake"], is_signer=False, is_writable=True
        ),
        AccountMeta(pubkey=accounts["user_stats"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["authority"], is_signer=True, is_writable=False),
        AccountMeta(
            pubkey=accounts["insurance_fund_vault"], is_signer=False, is_writable=True
        ),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\x8eF\xcc\\Ij\xb44"
    encoded_args = layout.build(
        {
            "market_index": args["market_index"],
            "amount": args["amount"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
