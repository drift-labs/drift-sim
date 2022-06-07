import pandas as pd
import numpy as np
from dataclasses import dataclass, field
 

@dataclass
class FeeStructure:
    numerator: int 
    denominator: int 
