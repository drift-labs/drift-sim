protocol_path=$1 
db_path=$2

solana-keygen new -o $(pwd)/anchor.json --silent --force --no-bip39-passphrase && 
export ANCHOR_WALLET=$(pwd)/anchor.json && 

clearinghouse_id=$(cat $protocol_path/programs/drift/src/lib.rs | grep declare_id! | tail -n 1) &&
clearinghouse_id=${clearinghouse_id:13:43} && 

pyth_id=$(cat $protocol_path/programs/pyth/src/lib.rs | grep declare_id! | tail -n 1) &&
pyth_id=${pyth_id:13:43} && 

echo pyth_id: $pyth_id
echo clearing_house: $clearinghouse_id
echo mint_pk $(solana-keygen pubkey $ANCHOR_WALLET)

~/.local/share/solana/install/releases/1.11.1/solana-release/bin/solana-test-validator -r \
--bpf-program $clearinghouse_id $protocol_path/target/deploy/drift.so \
--bpf-program $pyth_id $protocol_path/target/deploy/pyth.so \
--mint $(solana-keygen pubkey $ANCHOR_WALLET) \
--geyser-plugin-config $db_path/config.json
