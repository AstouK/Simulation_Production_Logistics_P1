import re
import numpy as np
import pandas as pd

# Format time
def format_time(minutes):
    hours = int(minutes // 60) % 24
    mins = int(minutes % 60)
    return f"{hours:02d}:{mins:02d}"

def parse_duration(val):
    """
    Parse a string like 'normal(90,10)' or 'uniform(40,60)' and return a sampled float value.
    """
    val = str(val).strip().lower()

    if val.startswith("uniform"):
        # Extract two numbers: lower and upper bound
        a, b = map(float, re.findall(r"[-+]?\d*\.\d+|\d+", val))
        return np.random.uniform(a, b)

    elif val.startswith("normal"):
        # Extract two numbers: mean and std dev
        mu, sigma = map(float, re.findall(r"[-+]?\d*\.\d+|\d+", val))
        return np.random.normal(mu, sigma)

    elif val.replace('.', '', 1).isdigit():
        # If it's already a number as a string like "30"
        return float(val)

    else:
        raise ValueError(f"Unrecognized duration format: '{val}'")
