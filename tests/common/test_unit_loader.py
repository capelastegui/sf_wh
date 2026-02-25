"""Tests for sf_wh.utils.unit_loader."""
import unittest
from pathlib import Path
from unittest.mock import call, patch

from sf_wh.common.unit_loader import (
    read_unit_csv,
    read_unit_point,
    read_unit_rules,
    read_unit_weapons,
)

_RULES_DIR = Path(__file__).parent.parent / 'sf_wh' / 'rules'


_UNIT_RULES_COLUMNS = [
    'faction', 'army', 'unit', 'model', 'is_inf', 'n_models',
    'T', 'SV', 'SV_invul', 'W', 'FNP',
    'minus_hit', 'minus_w', 'D_subtract', 'D_halve', 'rr_save',
]
_UNIT_POINTS_COLUMNS = ['unit_name', 'size', 'points']
_UNIT_WEAPONS_COLUMNS = [
    'faction', 'army', 'family', 'type', 'unit', 'model',
    'is_melee', 'name', 'mode', 'is_half_range',
    'R', 'A', 'H', 'S', 'AP', 'D_fixed', 'D_n_dice', 'D_dice_size',
    'rapid_fire', 'blast', 'melta', 'sustained_hits', 'letal_hits', 'dev_w',
    'anti_inf', 'anti_tank', 'ignore_cover', 'rr_hit', 'rr_wound',
    'bonus_hit', 'bonus_w',
]


class TestReadUnitCsv(unittest.TestCase):
    @patch('sf_wh.utils.unit_loader.pd.read_csv')
    def test_calls_read_csv_with_correct_path(self, mock_read_csv):
        read_unit_csv('gw', 'unit_rules_army1.csv')
        expected = _RULES_DIR / 'gw' / 'units' / 'unit_rules_army1.csv'
        mock_read_csv.assert_called_once_with(expected)

    @patch('sf_wh.utils.unit_loader.pd.read_csv')
    def test_returns_dataframe(self, mock_read_csv):
        result = read_unit_csv('gw', 'unit_rules_army1.csv')
        self.assertIs(result, mock_read_csv.return_value)

    def test_reads_real_csv(self):
        result = read_unit_csv('gw', 'unit_rules_army1.csv')
        self.assertIsNotNone(result)
        self.assertEqual(list(result.columns), _UNIT_RULES_COLUMNS)


class TestReadUnitRules(unittest.TestCase):
    @patch('sf_wh.utils.unit_loader.read_unit_csv')
    def test_default_ruleset(self, mock_read_unit_csv):
        read_unit_rules('army1')
        mock_read_unit_csv.assert_called_once_with('gw', 'unit_rules_army1.csv')

    @patch('sf_wh.utils.unit_loader.read_unit_csv')
    def test_custom_ruleset(self, mock_read_unit_csv):
        read_unit_rules('army1', ruleset='sf2')
        mock_read_unit_csv.assert_called_once_with('sf2', 'unit_rules_army1.csv')

    def test_reads_real_csv(self):
        result = read_unit_rules('army1', ruleset='gw')
        self.assertIsNotNone(result)
        self.assertEqual(list(result.columns), _UNIT_RULES_COLUMNS)


class TestReadUnitPoint(unittest.TestCase):
    @patch('sf_wh.utils.unit_loader.read_unit_csv')
    def test_default_ruleset(self, mock_read_unit_csv):
        read_unit_point('army1')
        mock_read_unit_csv.assert_called_once_with('gw', 'unit_points_army1.csv')

    @patch('sf_wh.utils.unit_loader.read_unit_csv')
    def test_custom_ruleset(self, mock_read_unit_csv):
        read_unit_point('army1', ruleset='sf2')
        mock_read_unit_csv.assert_called_once_with('sf2', 'unit_points_army1.csv')

    def test_reads_real_csv(self):
        result = read_unit_point('army1', ruleset='gw')
        self.assertIsNotNone(result)
        self.assertEqual(list(result.columns), _UNIT_POINTS_COLUMNS)


class TestReadUnitWeapons(unittest.TestCase):
    @patch('sf_wh.utils.unit_loader.read_unit_csv')
    def test_default_ruleset(self, mock_read_unit_csv):
        read_unit_weapons('army1')
        mock_read_unit_csv.assert_called_once_with('gw', 'unit_weapons_army1.csv')

    @patch('sf_wh.utils.unit_loader.read_unit_csv')
    def test_custom_ruleset(self, mock_read_unit_csv):
        read_unit_weapons('army1', ruleset='sf2')
        mock_read_unit_csv.assert_called_once_with('sf2', 'unit_weapons_army1.csv')

    def test_reads_real_csv(self):
        result = read_unit_weapons('army1', ruleset='gw')
        self.assertIsNotNone(result)
        self.assertEqual(list(result.columns), _UNIT_WEAPONS_COLUMNS)


if __name__ == '__main__':
    unittest.main()
