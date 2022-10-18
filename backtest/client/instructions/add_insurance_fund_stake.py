from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class AddInsuranceFundStakeArgs(typing.TypedDict):
    market_index: int
    amount: int


layout = borsh.CStruct("market_index" / borsh.U16, "amount" / borsh.U64)


class AddInsuranceFundStakeAccounts(typing.TypedDict):
    state: PublicKey
    spot_market: PublicKey
    insurance_fund_stake: PublicKey
    user_stats: PublicKey
    authority: PublicKey
    spot_market_vault: PublicKey
    insurance_fund_vault: PublicKey
    clearing_house_signer: PublicKey
    user_token_account: PublicKey
    token_program: PublicKey


def add_insurance_fund_stake(
    args: AddInsuranceFundStakeArgs,
    accounts: AddInsuranceFundStakeAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["state"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["spot_market"], is_signer=False, is_writable=False),
        AccountMeta(
            pubkey=accounts["insurance_fund_stake"], is_signer=False, is_writable=True
        ),
        AccountMeta(pubkey=accounts["user_stats"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["authority"], is_signer=True, is_writable=False),
        AccountMeta(
            pubkey=accounts["spot_market_vault"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["insurance_fund_vault"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["clearing_house_signer"], is_signer=False, is_writable=False
        ),
        AccountMeta(
            pubkey=accounts["user_token_account"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["token_program"], is_signer=False, is_writable=False
        ),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\xfb\x90s\x0b\xde/>\xec"
    encoded_args = layout.build(
        {
            "market_index": args["market_index"],
            "amount": args["amount"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
