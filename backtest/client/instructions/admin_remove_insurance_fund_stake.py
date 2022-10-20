from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class AdminRemoveInsuranceFundStakeArgs(typing.TypedDict):
    market_index: int
    amount: int


layout = borsh.CStruct("market_index" / borsh.U16, "amount" / borsh.U64)


class AdminRemoveInsuranceFundStakeAccounts(typing.TypedDict):
    admin: PublicKey
    state: PublicKey
    spot_market: PublicKey
    insurance_fund_vault: PublicKey
    clearing_house_signer: PublicKey
    admin_token_account: PublicKey
    token_program: PublicKey


def admin_remove_insurance_fund_stake(
    args: AdminRemoveInsuranceFundStakeArgs,
    accounts: AdminRemoveInsuranceFundStakeAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["admin"], is_signer=True, is_writable=False),
        AccountMeta(pubkey=accounts["state"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["spot_market"], is_signer=False, is_writable=False),
        AccountMeta(
            pubkey=accounts["insurance_fund_vault"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["clearing_house_signer"], is_signer=False, is_writable=False
        ),
        AccountMeta(
            pubkey=accounts["admin_token_account"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["token_program"], is_signer=False, is_writable=False
        ),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"#\ro\xdcg\xd9\xaes"
    encoded_args = layout.build(
        {
            "market_index": args["market_index"],
            "amount": args["amount"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
