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
    normalize_col,
    normalize_df,
    get_a,
    get_a_blast,
    get_a_rapid_fire,
    get_d_per_r,
    get_d_per_w_unsaved,
    get_d_to_k,
    get_df_atk_matrix,
    get_df_atk_report,
    get_prob_h,
    get_prob_save,
    get_prob_w,
    get_r_to_d,
    get_w_unsaved_per_a,
    get_k_per_r,
    get_r_to_k,
    process_D,
    roll_D,
    roll_n_dice,
    ATK_MATRIX_KEYS
)
from sf_wh.common.unit_loader import read_unit_rules, read_unit_weapons

# -- Globals

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pd.options.display.max_columns = 100
pd.options.display.width = 150
pd.set_option('display.expand_frame_repr', True)

_ATK_MATRIX_COLUMNS = [
    # from df_atk (unit_weapons)
    'faction', 'army', 'family', 'type', 'unit', 'model',
    'is_melee', 'name', 'mode', 'is_half_range',
    'R', 'A', 'H', 'S', 'AP', 'D_fixed', 'D_n_dice', 'D_dice_size',
    'rapid_fire', 'blast', 'melta', 'sustained_hits', 'lethal_hits', 'dev_w',
    'anti_inf', 'anti_tank', 'ignore_cover', 'rr_hit', 'rr_wound',
    'bonus_hit', 'bonus_w', 'crit_h', 'crit_w',
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
    'lethal_hits': _NAN, 'dev_w': _NAN, 'anti_inf': _NAN, 'anti_tank': _NAN,
    'ignore_cover': False, 'rr_hit': False, 'rr_wound': False, 'bonus_hit': 0, 'bonus_w': 0,
    'crit_h': 6, 'crit_w': 6,
}

_ATK_MATRIX_ROW_HEAVY_BOLTER = {
    'faction': 'imperium', 'army': 'any', 'family': 'Bolter', 'type': 'Basic',
    'unit': 'any', 'model': 'any', 'is_melee': False, 'name': 'Heavy Bolter',
    'mode': '-', 'is_half_range': False,
    'R': 36, 'A': 3, 'H': 3, 'S': 5, 'AP': 1, 'D_fixed': 2, 'D_n_dice': 0, 'D_dice_size': 0,
    'rapid_fire': _NAN, 'blast': _NAN, 'melta': _NAN, 'sustained_hits': 1,
    'lethal_hits': _NAN, 'dev_w': _NAN, 'anti_inf': _NAN, 'anti_tank': _NAN,
    'ignore_cover': False, 'rr_hit': False, 'rr_wound': False, 'bonus_hit': 0, 'bonus_w': 0,
    'crit_h': 6, 'crit_w': 6,
}

_DEF_MATRIX_ROW_GUARD = {
    'def_army': 'Astra Militarum', 'def_unit': 'Guard', 'def_model': _NAN,
    'is_inf': True, 'n_models': 1, 'T': 3, 'SV': 5, 'SV_invul': _NAN, 'W': 1, 'FNP': _NAN,
    'minus_hit': 0, 'minus_w': 0, 'D_subtract': 0, 'D_halve': False, 'rr_save': False,
}

_DEF_MATRIX_ROW_INTERCESSORS = {
    'def_army': 'Space Marines', 'def_unit': 'Intercessors', 'def_model': _NAN,
    'is_inf': True, 'n_models': 1, 'T': 4, 'SV': 3, 'SV_invul': _NAN, 'W': 2, 'FNP': _NAN,
    'minus_hit': 0, 'minus_w': 0, 'D_subtract': 0, 'D_halve': False, 'rr_save': False,
}

_DEF_MATRIX_ROW_TERMINATORS = {
    'def_army': 'Space Marines', 'def_unit': 'Terminators', 'def_model': _NAN,
    'is_inf': True, 'n_models': 1, 'T': 5, 'SV': 2, 'SV_invul': 4.0, 'W': 3, 'FNP': _NAN,
    'minus_hit': 0, 'minus_w': 0, 'D_subtract': 0, 'D_halve': False, 'rr_save': False,
}

_ATK_ROWS = [_ATK_MATRIX_ROW_BOLT_GUN, _ATK_MATRIX_ROW_HEAVY_BOLTER]
_DEF_ROWS = [_DEF_MATRIX_ROW_GUARD, _DEF_MATRIX_ROW_INTERCESSORS, _DEF_MATRIX_ROW_TERMINATORS]

# -- Functions

def log_info(msg, data):
    logger.info(msg + '\n' + str(data))

# -- Classes

class TestCombatRules(unittest.TestCase):
    df_atk = read_unit_weapons('army1', ruleset='test')
    df_def = read_unit_rules('army1', ruleset='test')
    df_atk_matrix = pd.merge(
        pd.DataFrame(_ATK_ROWS),
        pd.DataFrame(_DEF_ROWS),
        how='cross',
    )[_ATK_MATRIX_COLUMNS]

    def test_get_df_atk_matrix(self):
        result = get_df_atk_matrix(self.df_atk, self.df_def)
        self.assertEqual(len(result), len(self.df_atk) * len(self.df_def))
        self.assertEqual(list(result.columns), _ATK_MATRIX_COLUMNS)
        log_info('get_df_atk_matrix', result)

    def test_get_df_atk_report(self):
        result = get_df_atk_report(self.df_atk_matrix, pd.DataFrame(dict(c1=[1,2])))
        self.assertEqual(len(result), len(self.df_atk_matrix))
        self.assertEqual(list(result.columns), ATK_MATRIX_KEYS+['c1'])
        log_info('get_df_atk_matrix', result)

    def test_normalize_cols(self):
        s = pd.Series([10, 20])
        s_expected = pd.Series([1.,2.])
        s_result = normalize_col(s)
        pd.testing.assert_series_equal(s_result, s_expected)

    def test_normalize_df(self):
        df = get_df_atk_report(self.df_atk_matrix, pd.DataFrame(dict(c1=[1,2])))
        df_result = normalize_df(df)
        log_info('normalized df', df_result)

    def test_get_a_blast(self):
        result = get_a_blast(**self.df_atk_matrix)
        self.assertEqual(len(result), len(self.df_atk_matrix))
        log_info('get_a_blast', result)


    def test_get_a_rapid_fire(self):
        result = get_a_blast(**self.df_atk_matrix)
        self.assertEqual(len(result), len(self.df_atk_matrix))
        log_info('get_a_blast', result)

    def test_get_a(self):
        result = get_a(**self.df_atk_matrix)
        self.assertEqual(len(result), len(self.df_atk_matrix))
        log_info('get_a', result)

    def test_get_prob_h(self):
        result = get_prob_h(**self.df_atk_matrix)
        self.assertEqual(len(result), len(self.df_atk_matrix))
        self.assertEqual(list(result.columns), ['net_bonus', 'H_mod', 'prob_h', 'prob_crit_h'])
        log_info('get_prob_h', result)

    def test_get_prob_w(self):
        result = get_prob_w(**self.df_atk_matrix)
        self.assertEqual(len(result), len(self.df_atk_matrix))
        self.assertEqual(list(result.columns), ['div_s_t', 'prob_w', 'prob_crit_w'])
        log_info('get_prob_w', result)

    def test_get_prob_save(self):
        result = get_prob_save(**self.df_atk_matrix)
        self.assertEqual(len(result), len(self.df_atk_matrix))
        self.assertEqual(list(result.columns), ['cover_mod', 'min_save', 'sv_modified', 'prob_save'])
        log_info('get_prob_save', result)

    def test_get_w_unsaved_per_a(self):
        result = get_w_unsaved_per_a(self.df_atk_matrix)
        self.assertEqual(len(result), len(self.df_atk_matrix))
        self.assertEqual(result.name, 'prob_w_unsaved')
        self.assertFalse(result.isna().any())
        log_info('get_w_unsaved_per_a', result)

    def test_get_d_per_w_unsaved(self):
        result = get_d_per_w_unsaved(**self.df_atk_matrix)
        self.assertEqual(len(result), len(self.df_atk_matrix))
        self.assertEqual(list(result.columns), ['d', 'd_uncapped'])
        log_info('get_d_per_w_unsaved', result)

    # ---- Attack outcomes

    def test_get_d_per_r(self):
        result = get_d_per_r(self.df_atk_matrix)
        self.assertEqual(len(result), len(self.df_atk_matrix))
        log_info('get_d_per_r', result)

    def test_get_r_to_d(self):
        result = get_r_to_d(self.df_atk_matrix)
        self.assertEqual(len(result), len(self.df_atk_matrix))
        log_info('get_r_to_d', result)

    def test_get_d_to_k(self):
        # Scalar tests
        self.assertEqual(get_d_to_k(d=1, W=1), 1.0)
        self.assertEqual(get_d_to_k(d=1, W=2), 2.0)
        self.assertEqual(get_d_to_k(d=1, W=3), 3.0)
        self.assertEqual(get_d_to_k(d=3, W=2), 1.0)
        self.assertEqual(get_d_to_k(d=2, W=3), 2.0)
        self.assertEqual(get_d_to_k(d=3.5, W=4), 2.0)
        self.assertEqual(get_d_to_k(d=3.5, W=10), 3.0)

        # Vectorised tests
        result = get_d_to_k(1, **self.df_atk_matrix)
        self.assertEqual(len(result), len(self.df_atk_matrix))
        log_info('d_to_k', result)

    def test_get_k_per_r(self):
        result = get_k_per_r(self.df_atk_matrix)
        self.assertEqual(len(result), len(self.df_atk_matrix))
        log_info('k_per_r', result)

    def test_get_r_to_k(self):
        result = get_r_to_k(self.df_atk_matrix)
        self.assertEqual(len(result), len(self.df_atk_matrix))
        s_expected = pd.Series([2.25, 9., 40.5, 0.9, 1.8, 9.6])
        pd.testing.assert_series_equal(result, s_expected)
        log_info('r_to_k', result)

if __name__ == '__main__':
    unittest.main()
