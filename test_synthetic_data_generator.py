import unittest
from synthetic_data_generator import parse_value_name, KNOWN_VALUE_TYPE_SUFFIXES

class TestParseValueName(unittest.TestCase):

    def test_example_vis_vv_mv_ing(self):
        input_str = 'VIS_VV_Mätvärden\\VIS_VV_PLC1_CT15151_PV4.MV_ING'
        expected = {
            'original_string': input_str,
            'category_system': 'VIS_VV_Mätvärden',
            'group_location_prefix': 'VIS_VV',
            'plc_id': 'PLC1',
            'equipment_id_full': 'CT15151_PV4',
            'equipment_type_prefix': 'CT',
            'equipment_numeric_id': '15151',
            'equipment_suffix_property': 'PV4',
            'value_type_suffix': 'MV_ING'
        }
        result = parse_value_name(input_str)
        self.assertEqual(result, expected)

    def test_example_ts_driftid_drt(self):
        input_str = 'TS_Driftid\\MAR_TS_PLC1_AH13015_DS.DRT'
        expected = {
            'original_string': input_str,
            'category_system': 'TS_Driftid',
            'group_location_prefix': 'MAR_TS',
            'plc_id': 'PLC1',
            'equipment_id_full': 'AH13015_DS',
            'equipment_type_prefix': 'AH',
            'equipment_numeric_id': '13015',
            'equipment_suffix_property': 'DS',
            'value_type_suffix': 'DRT'
        }
        result = parse_value_name(input_str)
        self.assertEqual(result, expected)

    def test_example_el_effekt_ep(self): # suffix part of main ID (no dot)
        input_str = 'VIS_VV_El_Effekt_EP\\VIS_VV_PLC1_GH15051_EP'
        expected = {
            'original_string': input_str,
            'category_system': 'VIS_VV_El_Effekt_EP',
            'group_location_prefix': 'VIS_VV',
            'plc_id': 'PLC1',
            'equipment_id_full': 'GH15051',
            'equipment_type_prefix': 'GH',
            'equipment_numeric_id': '15051',
            'equipment_suffix_property': None,
            'value_type_suffix': 'EP'
        }
        result = parse_value_name(input_str)
        self.assertEqual(result, expected)

    def test_example_rr_reservoarer(self): # Complex suffix: RR.G3_MVF
        input_str = 'RR_Reservoarer\\BES_HR_PLC1_RR14200_RR.G3_MVF'
        # Current parser behavior: everything after the dot is value_type_suffix.
        # It does not further parse "RR.G3_MVF".
        expected = {
            'original_string': input_str,
            'category_system': 'RR_Reservoarer',
            'group_location_prefix': 'BES_HR',
            'plc_id': 'PLC1',
            'equipment_id_full': 'RR14200_RR',
            'equipment_type_prefix': 'RR',
            'equipment_numeric_id': '14200',
            'equipment_suffix_property': 'RR', # Property of the equipment
            'value_type_suffix': 'G3_MVF' # Everything after dot
        }
        result = parse_value_name(input_str)
        self.assertEqual(result, expected)

    def test_example_pro_vattenmangd_total_int(self):
        input_str = 'PRO_Vattenmängd\\ROG_IT_PLC1_CF19711_PL.Total_INT'
        expected = {
            'original_string': input_str,
            'category_system': 'PRO_Vattenmängd',
            'group_location_prefix': 'ROG_IT',
            'plc_id': 'PLC1',
            'equipment_id_full': 'CF19711_PL',
            'equipment_type_prefix': 'CF',
            'equipment_numeric_id': '19711',
            'equipment_suffix_property': 'PL',
            'value_type_suffix': 'Total_INT'
        }
        result = parse_value_name(input_str)
        self.assertEqual(result, expected)

    def test_no_dot_suffix_total(self):
        # Based on Test Case 6 from synthetic_data_generator.py
        # 'Category\Group_Loc_PLC_EQ123_Total'
        # Here, Total is a known suffix and should be identified even without a preceding dot.
        input_str = 'TS_Vattenmängd\\MAR_TS_PLC1_CF13111_PL_Total'
        expected = {
            'original_string': input_str,
            'category_system': 'TS_Vattenmängd',
            'group_location_prefix': 'MAR_TS',
            'plc_id': 'PLC1',
            'equipment_id_full': 'CF13111_PL',
            'equipment_type_prefix': 'CF',
            'equipment_numeric_id': '13111',
            'equipment_suffix_property': 'PL',
            'value_type_suffix': 'Total'
        }
        result = parse_value_name(input_str)
        self.assertEqual(result, expected)

    def test_short_id_no_property(self): # e.g. AH vs CT in examples.
        input_str = 'TS_Driftid\\TOF_TS_PLC1_AP14702_FC.DRT'
        expected = {
            'original_string': input_str,
            'category_system': 'TS_Driftid',
            'group_location_prefix': 'TOF_TS',
            'plc_id': 'PLC1',
            'equipment_id_full': 'AP14702_FC', # FC is property of AP14702
            'equipment_type_prefix': 'AP',
            'equipment_numeric_id': '14702',
            'equipment_suffix_property': 'FC',
            'value_type_suffix': 'DRT'
        }
        result = parse_value_name(input_str)
        self.assertEqual(result, expected)

    def test_minimal_structure(self): # Similar to VIS_VV but different values
        input_str = 'VMB_Mätvärden\\NOR_VMB_PLC1_CP18281_PV4.MV_ING'
        expected = {
            'original_string': input_str,
            'category_system': 'VMB_Mätvärden',
            'group_location_prefix': 'NOR_VMB',
            'plc_id': 'PLC1',
            'equipment_id_full': 'CP18281_PV4',
            'equipment_type_prefix': 'CP',
            'equipment_numeric_id': '18281',
            'equipment_suffix_property': 'PV4',
            'value_type_suffix': 'MV_ING'
        }
        result = parse_value_name(input_str)
        self.assertEqual(result, expected)

    def test_only_category_and_plc_equip_dot_suffix(self):
        input_str = 'Category\\PLC_Equip.Suffix'
        # Based on test case 5 from synthetic_data_generator.py, but simplified group/plc
        # Current logic for mpc_len=2: plc=mpc[0], equip=mpc[1]
        expected = {
            'original_string': input_str,
            'category_system': 'Category',
            'group_location_prefix': None, # Because mpc will be ['PLC','Equip'], len 2
            'plc_id': 'PLC',
            'equipment_id_full': 'Equip',
            'equipment_type_prefix': 'Eq', # Assuming 'Eq' from 'Equip'
            'equipment_numeric_id': None, # Assuming 'uip' is not numeric
            'equipment_suffix_property': None,
            'value_type_suffix': 'Suffix'
        }
        result = parse_value_name(input_str)
        self.assertEqual(result, expected)

    def test_only_category_and_plc_equip_underscore_suffix(self):
        input_str = 'Category\\PLC_Equip_EP' # EP is a known suffix
        # mpc after suffix: ['PLC', 'Equip']
        expected = {
            'original_string': input_str,
            'category_system': 'Category',
            'group_location_prefix': None,
            'plc_id': 'PLC',
            'equipment_id_full': 'Equip',
            'equipment_type_prefix': 'Eq',
            'equipment_numeric_id': None,
            'equipment_suffix_property': None,
            'value_type_suffix': 'EP'
        }
        result = parse_value_name(input_str)
        self.assertEqual(result, expected)

    def test_unparseable_string(self):
        input_str = 'Hello\\World_Test_ABC.Value' # Does not fit dominant G1_G2_P_E pattern
        # Based on current logic:
        # category_system = 'Hello'
        # main_part = 'World_Test_ABC' (value_type_suffix = 'Value')
        # mpc = ['World', 'Test', 'ABC']
        # mpc_len = 3. Heuristic for mpc_len=3:
        # is_mpc0_long_or_mixed_case ('World' len > 3) = True
        # So, grp = mpc[0] = 'World'
        # plc = mpc[1] = 'Test'
        # eq_id = mpc[2] = 'ABC'
        expected = {
            'original_string': input_str,
            'category_system': 'Hello',
            'group_location_prefix': 'World',
            'plc_id': 'Test',
            'equipment_id_full': 'ABC',
            'equipment_type_prefix': 'AB', # From 'ABC'
            'equipment_numeric_id': None, # 'C' is not numeric
            'equipment_suffix_property': None,
            'value_type_suffix': 'Value'
        }
        result = parse_value_name(input_str)
        self.assertEqual(result, expected)

    def test_string_without_backslash_and_known_suffix(self):
        # Test Case 7 from synthetic_data_generator.py
        input_str = 'PROJ_Alarmnivåer_EP'
        expected = {
            'original_string': input_str,
            'category_system': 'PROJ_Alarmnivåer_EP',
            'group_location_prefix': None,
            'plc_id': None,
            'equipment_id_full': 'PROJ_Alarmnivåer',
            'equipment_type_prefix': None, # 'PROJ_Alarmnivåer' parsing
            'equipment_numeric_id': None,
            'equipment_suffix_property': None,
            'value_type_suffix': 'EP'
        }
        result = parse_value_name(input_str)
        # Refined expectation for 'PROJ_Alarmnivåer' equipment parsing:
        # first_eq_part = 'PROJ'. equipment_type_prefix = 'PR'. numeric_id = None (OJ not num)
        # suffix_property = 'Alarmnivåer'
        # This depends on how un-prefixed equipment IDs are handled.
        # The current code for equip id "PROJ_Alarmnivåer":
        # eq_parts = ['PROJ', 'Alarmnivåer']
        # first_eq_part = 'PROJ'
        # it's not AA12345, not all digits.
        # len('PROJ') >=2 and 'PR'.isalpha() -> True. prefix='PR'. numeric_id = None.
        # suffix_property = 'Alarmnivåer'.
        expected['equipment_type_prefix'] = 'PR'
        expected['equipment_suffix_property'] = 'Alarmnivåer'
        self.assertEqual(result, expected)

    def test_string_with_no_equipment_id(self):
        # Test Case 8 from synthetic_data_generator.py
        input_str = 'VIS_VV_Mätvärden\\VIS_VV_PLC1.MV_ING'
        expected = {
            'original_string': input_str,
            'category_system': 'VIS_VV_Mätvärden',
            'group_location_prefix': 'VIS_VV',
            'plc_id': 'PLC1',
            'equipment_id_full': None,
            'equipment_type_prefix': None,
            'equipment_numeric_id': None,
            'equipment_suffix_property': None,
            'value_type_suffix': 'MV_ING'
        }
        result = parse_value_name(input_str)
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()
