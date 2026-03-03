"""
unit_loader - Helpers for loading unit CSV files from the rules directory.
"""

# -- Public Imports

from pathlib import Path

import pandas as pd

# -- Private Imports

# -- Globals

_RULES_DIR = Path(__file__).parent.parent / 'rules'
_TEST_DATA_DIR = Path(__file__).parent.parent.parent / 'tests' / 'data'

# -- Functions

def read_unit_csv(ruleset, file_name):
    """Read a CSV file from [ruleset]/units/ and return a DataFrame."""
    if ruleset == 'test':
        path = _TEST_DATA_DIR / 'units' / file_name
    else:
        path = _RULES_DIR / ruleset / 'units' / file_name
    return pd.read_csv(path)


def read_unit_rules(army, ruleset='gw'):
    """Read unit_rules_[army].csv for the given ruleset."""
    return read_unit_csv(ruleset, f'unit_rules_{army}.csv')


def read_unit_point(army, ruleset='gw'):
    """Read unit_points_[army].csv for the given ruleset."""
    return read_unit_csv(ruleset, f'unit_points_{army}.csv')


def read_unit_weapons(army, ruleset='gw'):
    """Read unit_weapons_[army].csv for the given ruleset."""
    return read_unit_csv(ruleset, f'unit_weapons_{army}.csv')

# -- Classes
