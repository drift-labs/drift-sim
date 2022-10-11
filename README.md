## QuickStart

## install python packages 
```bash
# creates a virtualenv called "venv"
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# setup other submodules
bash setup.sh 
```

## run an example 

- `sim_eval.ipynb`

## update scripts

```
git submodule update --remote --merge
pip install driftpy/ --upgrade
```

## future work
- split test.py to tests/*_test.py
- complete/recon full implementation of programs/clearing_house (from rust implementation)