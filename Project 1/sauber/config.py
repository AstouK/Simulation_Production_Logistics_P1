import pandas as pd
import numpy as np

# Constants
SIM_TIME = 9 * 5 * 60  # 2250 hours in minutes
OPERATING_HOURS = 9
START_OF_DAY = 8 * 60
WORKDAY_MINUTES = OPERATING_HOURS * 60

# Laundry types
laundry_types = pd.DataFrame({
    "Type": ["Boil-wash", "Colored wash", "Delicate wash", "Wool"],
    "Share": [0.4, 0.3, 0.2, 0.1],
    "Washing Time": ["normal(90,10)", "normal(60,10)", "uniform(40,60", 30], # distribution as string for simulation to create new values evry time
    "Dryer Type": ["Normal", "Normal", "Normal", "Special"],
    "Drying Time": ["uniform(60,90)", "normal(40,10)", "normal(50,15)", "uniform(30,40)"],
    "Ironing": [True, True, False, False],
})