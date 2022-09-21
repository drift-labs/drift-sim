`main.py`: main backtest file 

example command (ran from within backtest/): `python main.py --events tmp2 --protocol ../driftpy/protocol-v2 `

note: make sure `anchor localnet` works in protocol directory

note: run `ps aux | grep solana` to kill rogue validators

# generating sim events 
- run `workspace/collateral_check.py`