# %%
import psycopg2
import pandas as pd 
from solana.publickey import PublicKey
from anchorpy import Program
from solana.publickey import PublicKey
from pathlib import Path 
from anchorpy import Idl 
import json 
import re 
import sys
sys.path.insert(0, '../driftpy/src/')

sys.path.insert(0, '../')
from backtest.helpers import serialize_perp_market_2
from spl.token._layouts import ACCOUNT_LAYOUT

import json
from driftpy.addresses import * 

def read_sql_db():
    conn = psycopg2.connect(
        host="localhost", 
        database="solana",
        user="solana"
    )
    cur = conn.cursor()

    cmd = """
    select * from account
    union 
    select * from account_audit
    order by slot, write_version asc
    """

    df = pd.read_sql_query(cmd, conn)
    print("# of examples found:", len(df))

    cur.close()
    conn.close()

    # parsing sql list[bytes] to bytes of pk + account data
    datas = []
    pks = []
    for _, row in df.iterrows():
        pk = row.pubkey
        pk = PublicKey(b''.join([pk[i] for i in range(pk.nbytes)]))
        pks.append(str(pk))

        data = row.data
        data = b''.join([data[i] for i in range(data.nbytes)])
        datas.append(data)

    df['_data'] = datas
    df['pk'] = pks

    return df 

def get_program(v2_path):
    with open(f'{v2_path}/programs/clearing_house/src/lib.rs', 'r') as f:
        data = f.read()
    re_result = re.search('\[cfg\(not\(feature = \"mainnet-beta\"\)\)\]\ndeclare_id!\(\"(.*)\"\)', data)
    program_id = PublicKey(re_result.group(1))

    file = Path(f'{v2_path}/target/idl/clearing_house.json')
    with file.open() as f:
        idl_dict = json.load(f)
    idl = Idl.from_json(idl_dict)
    program = Program(idl, program_id, None)
    return program

class Extractor:
    def __init__(self, df, program, save_path) -> None:
        self.df = df
        self.program = program
        self.save_path = save_path

    def decode_type_to_object(self, pk, type):
        type_rows = self.df[self.df['pk'] == str(pk)]
        type_history = []
        rows = []
        for i, r in type_rows.iterrows():
            data = r['_data']
            type_obj = self.program.account[type]._coder.accounts.parse(data).data
            type_history.append(type_obj)
            rows.append(r)
        return type_history, rows
 
    def extract_token_account(self, pk: PublicKey, name: str):
        i = 0 # only one supported rn

        vaults = []
        type_rows = self.df[self.df['pk'] == str(pk)]
        for _, r in type_rows.iterrows():
            data = r['_data']
            obj = ACCOUNT_LAYOUT.parse(data)
            obj = dict(obj) 
            obj.pop('_io')

            # todo things 
            # add time information to dict
            obj['slot'] = r['slot']
            obj['write_version'] = r['write_version']
            obj['updated_on'] = r['updated_on']

            vaults.append(obj)

        vault_df = pd.DataFrame(vaults)
        vault_df.to_csv(self.save_path/f"{name}_{i}.csv", index=False)

    def extract_perp_market(self, pk: PublicKey, i: int):
        perp_market_history, rows = self.decode_type_to_object(pk, 'PerpMarket')
        perp_market_df = []
        for perp_market, r in zip(perp_market_history, rows):
            perp_df = serialize_perp_market_2(perp_market)

            # add time information to dict
            perp_df['slot'] = r['slot']
            perp_df['write_version'] = r['write_version']
            perp_df['updated_on'] = r['updated_on']

            perp_market_df.append(perp_df)

        perp_market_df = pd.concat(perp_market_df)
        perp_market_df.to_csv(self.save_path/f"perp_market_{i}.csv", index=False)

    def extract_state_account(self, pk):
        i = 0
        
        state_history, rows = self.decode_type_to_object(pk, 'State')
        state_df = []
        for state, r in zip(state_history, rows):
            d = state.__dict__
            # todo do things
                    
            # add time information to dict
            d['slot'] = r['slot']
            d['write_version'] = r['write_version']
            d['updated_on'] = r['updated_on']

            state_df.append(d)
        state_df = pd.DataFrame(state_df)
        state_df.to_csv(self.save_path/f"state_{i}.csv", index=False)

    def extract_user(self, pk: PublicKey, i: int):
        user_history, user_rows = self.decode_type_to_object(pk, "User")
        user_df = []
        for user, r in zip(user_history, user_rows):
            d = user.__dict__

            # add time information to dict
            d['slot'] = r['slot']
            d['write_version'] = r['write_version']
            d['updated_on'] = r['updated_on']

            user_df.append(d)

        user_df = pd.DataFrame(user_df)
        user_df.to_csv(self.save_path/f"user_{i}.csv", index=False)

    def extract_user_stats(self, pk: PublicKey, i: int):
        user_stats_history, stats_rows = self.decode_type_to_object(pk, "UserStats")
        user_stats_df = []
        for user_s, r in zip(user_stats_history, stats_rows):
            d = user_s.__dict__

            # add time information to dict
            d['slot'] = r['slot']
            d['write_version'] = r['write_version']
            d['updated_on'] = r['updated_on']

            # todo do things
            user_stats_df.append(d)

        user_stats_df = pd.DataFrame(user_stats_df)
        user_stats_df.to_csv(self.save_path/f"user_stats_{i}.csv", index=False)

def main(
    v2_path: str,
    save_path: Path,
    user_path: str, 
    state_path: str,
):
    print('saving to:', save_path.absolute())

    print('=> starting sql geyser export...')
    df = read_sql_db()
    program = get_program(v2_path)
    program_id = program.program_id

    extractor = Extractor(df, program, save_path)

    with open(user_path, 'r') as f:
        users = json.load(f)

    with open(state_path, 'r') as f:
        state = json.load(f)

    n_markets = state['number_of_markets']
    n_spot_markets = state['number_of_spot_markets']

    if n_spot_markets != 1:
        print('WARNING: only 1 spot market sims fully supported...')

    user_auths = [PublicKey(u) for u in users.values()]
    users = [get_user_account_public_key(program_id, auth) for auth in user_auths]
    user_stats = [
        get_user_stats_account_public_key(program_id, pk)
        for pk in user_auths
    ]
    perp_markets = [
        get_perp_market_public_key(program_id, i) for i in range(n_markets)
    ]
    state = get_state_public_key(program_id)

    # vaults 
    i = 0
    spot_vault_public_key = get_spot_market_vault_public_key(program_id, i)
    insurance_vault_public_key = get_insurance_fund_vault_public_key(program_id, i)

    extractor.extract_token_account(spot_vault_public_key, 'spot_vault')
    extractor.extract_token_account(insurance_vault_public_key, 'insurance_vault')
    extractor.extract_state_account(state)

    for i, pk in enumerate(perp_markets):
        extractor.extract_perp_market(pk, i)

    for i, (user, user_stat) in enumerate(zip(users, user_stats)):
        extractor.extract_user(user, i)
        extractor.extract_user_stats(user_stat, i)

    print('done!')

if __name__ == '__main__':
    v2_path = '../driftpy/protocol-v2'
    experiment_name = 'simple'
    experiment_type_name = 'trial_no_oracle_guards'

    user_path = f'../experiments/results/{experiment_name}/{experiment_type_name}/users.json'
    state_path = f'../experiments/results/{experiment_name}/{experiment_type_name}/init_state.json'
    results_path = f'../experiments/results/{experiment_name}/{experiment_type_name}/data/'
    Path(results_path).mkdir(exist_ok=True, parents=True)

    main(
        v2_path, 
        results_path, 
        user_path,
        state_path
    )