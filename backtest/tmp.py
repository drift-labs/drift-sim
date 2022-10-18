#%%
import pandas as pd 
import seaborn as sns
sns.set()

leverages = pd.read_csv('tmp.csv')
leverages.plot()

#%%
with open('../driftpy/protocol-v2/programs/clearing_house/src/lib.rs', 'r') as f:
    data = f.read()
import re 
result = re.search('\[cfg\(not\(feature = \"mainnet-beta\"\)\)\]\ndeclare_id!\(\"(.*)\"\)', data)
id = result.group(1)
id

#%%
events = pd.read_csv('lunaCrash/events.csv')

event_names = list(events['event_name'].unique())
event_names.pop(event_names.index('oracle_price'))

import matplotlib.pyplot as plt 
import numpy as np 

oracle_event_stamps = events[events['event_name'] == 'oracle_price']['timestamp'].values
plt.scatter(oracle_event_stamps, np.zeros_like(oracle_event_stamps), label='oracle')

i = 1
for event in event_names:
    event_stamps = events[events['event_name'] == event]['timestamp'].values
    plt.scatter(event_stamps, np.zeros_like(event_stamps) + i, label=event)
    i += 1

plt.title('event timestamps')
plt.legend()
plt.show()

#%%
#%%