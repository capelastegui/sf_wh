"""Tests for sf_wh.utils.unit_loader."""
import unittest
from pathlib import Path
from unittest.mock import call, patch

from sf_wh.utils.unit_loader import (
    read_unit_csv,
    read_unit_point,
    read_unit_rules,
    read_unit_weapons,
)

_RULES_DIR = Path(__file__).parent.parent / 'sf_wh' / 'rules'


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


class TestReadUnitRules(unittest.TestCase):
    @patch('sf_wh.utils.unit_loader.read_unit_csv')
    def test_default_ruleset(self, mock_read_unit_csv):
        read_unit_rules('army1')
        mock_read_unit_csv.assert_called_once_with('gw', 'unit_rules_army1.csv')

    @patch('sf_wh.utils.unit_loader.read_unit_csv')
    def test_custom_ruleset(self, mock_read_unit_csv):
        read_unit_rules('army1', ruleset='sf2')
        mock_read_unit_csv.assert_called_once_with('sf2', 'unit_rules_army1.csv')


class TestReadUnitPoint(unittest.TestCase):
    @patch('sf_wh.utils.unit_loader.read_unit_csv')
    def test_default_ruleset(self, mock_read_unit_csv):
        read_unit_point('army1')
        mock_read_unit_csv.assert_called_once_with('gw', 'unit_points_army1.csv')

    @patch('sf_wh.utils.unit_loader.read_unit_csv')
    def test_custom_ruleset(self, mock_read_unit_csv):
        read_unit_point('army1', ruleset='sf2')
        mock_read_unit_csv.assert_called_once_with('sf2', 'unit_points_army1.csv')


class TestReadUnitWeapons(unittest.TestCase):
    @patch('sf_wh.utils.unit_loader.read_unit_csv')
    def test_default_ruleset(self, mock_read_unit_csv):
        read_unit_weapons('army1')
        mock_read_unit_csv.assert_called_once_with('gw', 'unit_weapons_army1.csv')

    @patch('sf_wh.utils.unit_loader.read_unit_csv')
    def test_custom_ruleset(self, mock_read_unit_csv):
        read_unit_weapons('army1', ruleset='sf2')
        mock_read_unit_csv.assert_called_once_with('sf2', 'unit_weapons_army1.csv')


if __name__ == '__main__':
    unittest.main()
