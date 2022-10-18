from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from .. import types
from ..program_id import PROGRAM_ID


class UpdatePerpMarketContractTierArgs(typing.TypedDict):
    contract_tier: types.contract_tier.ContractTierKind


layout = borsh.CStruct("contract_tier" / types.contract_tier.layout)


class UpdatePerpMarketContractTierAccounts(typing.TypedDict):
    admin: PublicKey
    state: PublicKey
    perp_market: PublicKey


def update_perp_market_contract_tier(
    args: UpdatePerpMarketContractTierArgs,
    accounts: UpdatePerpMarketContractTierAccounts,
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
    identifier = b"\xec\x80\x0f_\xcb\xd6Du"
    encoded_args = layout.build(
        {
            "contract_tier": args["contract_tier"].to_encodable(),
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
