"""
test_combat_rules - Tests for sf_wh.common.combat_rules.
"""

# -- Public Imports

import logging
import unittest

import pandas as pd

# -- Private Imports

from sf_wh.common.combat_rules import (
    cartesian_product_itertools,
    get_df_atk_matrix,
    get_w_unsaved_per_a,
    get_prob_h,
    get_prob_save,
    get_prob_w,
    get_r_to_k,
    process_D,
    roll_D,
    roll_n_dice,
    get_d_per_w_unsaved
)
from sf_wh.common.unit_loader import read_unit_rules, read_unit_weapons

# -- Globals

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_ATK_MATRIX_COLUMNS = [
    # from df_atk (unit_weapons)
    'faction', 'army', 'family', 'type', 'unit', 'model',
    'is_melee', 'name', 'mode', 'is_half_range',
    'R', 'A', 'H', 'S', 'AP', 'D_fixed', 'D_n_dice', 'D_dice_size',
    'rapid_fire', 'blast', 'melta', 'sustained_hits', 'letal_hits', 'dev_w',
    'anti_inf', 'anti_tank', 'ignore_cover', 'rr_hit', 'rr_wound',
    'bonus_hit', 'bonus_w',
    # from df_def (unit_rules), faction dropped, army/unit/model renamed
    'def_army', 'def_unit', 'def_model',
    'is_inf', 'n_models', 'T', 'SV', 'SV_invul', 'W', 'FNP',
    'minus_hit', 'minus_w', 'D_subtract', 'D_halve', 'rr_save',
]

_NAN = float('nan')

_ATK_MATRIX_ROW_BOLT_GUN = {
    'faction': 'imperium', 'army': 'any', 'family': 'Bolter', 'type': 'Basic',
    'unit': 'any', 'model': 'any', 'is_melee': False, 'name': 'Bolt gun',
    'mode': '-', 'is_half_range': False,
    'R': 24, 'A': 2, 'H': 3, 'S': 4, 'AP': 0, 'D_fixed': 1, 'D_n_dice': 0, 'D_dice_size': 0,
    'rapid_fire': _NAN, 'blast': _NAN, 'melta': _NAN, 'sustained_hits': _NAN,
    'letal_hits': _NAN, 'dev_w': _NAN, 'anti_inf': _NAN, 'anti_tank': _NAN,
    'ignore_cover': False, 'rr_hit': False, 'rr_wound': False, 'bonus_hit': 0, 'bonus_w': 0,
}

# -- Functions

def log_info(msg, data):
    logger.info(msg + '\n' + str(data))

# -- Classes

class TestCombatRules(unittest.TestCase):
    df_atk = read_unit_weapons('army1', ruleset='test')
    df_def = read_unit_rules('army1', ruleset='test')
    df_atk_matrix = pd.DataFrame([
        {
            **_ATK_MATRIX_ROW_BOLT_GUN,
            'def_army': 'Space Marines', 'def_unit': 'Intercessors', 'def_model': _NAN,
            'is_inf': True, 'n_models': 1, 'T': 4, 'SV': 3, 'SV_invul': _NAN, 'W': 2, 'FNP': _NAN,
            'minus_hit': 0, 'minus_w': 0, 'D_subtract': 0, 'D_halve': False, 'rr_save': False,
        },
        {
            **_ATK_MATRIX_ROW_BOLT_GUN,
            'def_army': 'Space Marines', 'def_unit': 'Terminators', 'def_model': _NAN,
            'is_inf': True, 'n_models': 1, 'T': 5, 'SV': 2, 'SV_invul': 4.0, 'W': 3, 'FNP': _NAN,
            'minus_hit': 0, 'minus_w': 0, 'D_subtract': 0, 'D_halve': False, 'rr_save': False,
        },
    ], columns=_ATK_MATRIX_COLUMNS)

    def test_get_df_atk_matrix(self):
        result = get_df_atk_matrix(self.df_atk, self.df_def)
        self.assertEqual(len(result), len(self.df_atk) * len(self.df_def))
        self.assertEqual(list(result.columns), _ATK_MATRIX_COLUMNS)
        log_info('get_df_atk_matrix', result)

    def test_get_prob_save(self):
        result = get_prob_save(**self.df_atk_matrix)
        self.assertEqual(len(result), len(self.df_atk_matrix))
        self.assertEqual(list(result.columns), ['cover_mod', 'min_save', 'sv_modified', 'prob_save'])
        log_info('get_prob_save', result)

    def test_get_prob_h(self):
        result = get_prob_h(**self.df_atk_matrix)
        self.assertEqual(len(result), len(self.df_atk_matrix))
        self.assertEqual(list(result.columns), ['net_bonus', 'H_mod', 'prob_h'])
        log_info('get_prob_h', result)

    def test_get_prob_w(self):
        result = get_prob_w(**self.df_atk_matrix)
        self.assertEqual(len(result), len(self.df_atk_matrix))
        self.assertEqual(list(result.columns), ['div_s_t', 'prob_w'])
        log_info('get_prob_w', result)

    def test_get_prob_dmg(self):
        result = get_w_unsaved_per_a(self.df_atk_matrix)
        self.assertEqual(len(result), len(self.df_atk_matrix))
        self.assertEqual(list(result.columns), ['prob_dmg'])
        log_info('get_prob_dmg', result)

    def test_get_avg_d_roll_placeholder(self):
        result = get_d_per_w_unsaved(**self.df_atk_matrix)
        self.assertEqual(len(result), len(self.df_atk_matrix))
        self.assertEqual(list(result.columns), ['dmg', 'dmg_uncapped'])
        log_info('get_prob_dmg', result)

    def test_get_r_to_k(self):
        result = get_r_to_k(self.df_atk_matrix)
        self.assertEqual(len(result), len(self.df_atk_matrix))
        self.assertEqual(list(result.columns), ['r_to_k'])
        log_info('r_to_k', result)

if __name__ == '__main__':
    unittest.main()
