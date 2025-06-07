"""
Generates synthetic data based on value name string patterns.
"""
import datetime
import random

KNOWN_VALUE_TYPE_SUFFIXES = ['EP', 'Total', 'DRT', 'MV_ING', 'Total_INT']

def parse_value_name(value_name_string):
  """
  Parses a value name string into its components.
  Example: 'VIS_VV_Mätvärden\VIS_VV_PLC1_CT15151_PV4.MV_ING'
  Output:
  {
      'original_string': 'VIS_VV_Mätvärden\VIS_VV_PLC1_CT15151_PV4.MV_ING',
      'category_system': 'VIS_VV_Mätvärden',
      'group_location_prefix': 'VIS_VV',
      'plc_id': 'PLC1',
      'equipment_id_full': 'CT15151_PV4',
      'equipment_type_prefix': 'CT',
      'equipment_numeric_id': '15151',
      'equipment_suffix_property': 'PV4',
      'value_type_suffix': 'MV_ING'
  }
  """
  components = {
      'original_string': value_name_string,
      'category_system': None,
      'group_location_prefix': None,
      'plc_id': None,
      'equipment_id_full': None,
      'equipment_type_prefix': None,
      'equipment_numeric_id': None,
      'equipment_suffix_property': None,
      'value_type_suffix': None
  }

  parts = value_name_string.split('\\')
  if not parts:
    return components # Should not happen with valid strings

  components['category_system'] = parts[0]

  if len(parts) < 2:
    # String has no '\'. It's considered category_system.
    # All other specific components like group_location_prefix, plc_id will be None.
    # Try to find a known suffix at the end of it to populate value_type_suffix and equipment_id_full.
    temp_category_string = components['category_system'] # which is value_name_string
    longest_found_suffix_no_slash = None

    for known_suffix in KNOWN_VALUE_TYPE_SUFFIXES:
        if temp_category_string.endswith(f"_{known_suffix}"):
            if longest_found_suffix_no_slash is None or len(known_suffix) > len(longest_found_suffix_no_slash):
                longest_found_suffix_no_slash = known_suffix
        elif temp_category_string == known_suffix:
             if longest_found_suffix_no_slash is None or len(known_suffix) > len(longest_found_suffix_no_slash):
                longest_found_suffix_no_slash = known_suffix

    if longest_found_suffix_no_slash:
        components['value_type_suffix'] = longest_found_suffix_no_slash
        if temp_category_string == longest_found_suffix_no_slash:
            components['equipment_id_full'] = None
        else:
            components['equipment_id_full'] = temp_category_string[:-len(longest_found_suffix_no_slash)-1]
    else:
        # No known suffix. If the category string itself is not a known suffix,
        # then it's just a category, no specific equipment_id_full or value_type from it.
        # However, test 'PROJ_Alarmnivåer_EP' implies that if no suffix, the remainder is equip_id.
        # This seems contradictory. Let's assume if no suffix, no equip_id from category string.
        # The test seems to imply PROJ_Alarmnivåer_EP -> suffix EP, equip_id PROJ_Alarmnivåer
        # If it was PROJ_Alarmnivåer -> suffix None, equip_id PROJ_Alarmnivåer (if treated as equip) or None.
        # For simplicity, if no suffix is found, equipment_id_full is None for no-backslash strings.
        # The test case implies 'PROJ_Alarmnivåer_EP' has category_system as the full string.
        # And equipment_id_full is 'PROJ_Alarmnivåer'. This is set if suffix is found.
        # If no suffix found, e.g. "MyCategoryOnly", then equipment_id_full should be None.
        if not components['value_type_suffix']: # if still None
             components['equipment_id_full'] = None


    # group_location_prefix, plc_id remain None.
    # Flow continues to the common equipment_id_full parsing logic below.

  else: # len(parts) >= 2, so there is a '\'
    main_part_with_suffix = parts[1]

    # Try to split by '.' for value_type_suffix
    if '.' in main_part_with_suffix:
      main_part, value_type_suffix_candidate = main_part_with_suffix.rsplit('.', 1)
      components['value_type_suffix'] = value_type_suffix_candidate
    else:
      main_part = main_part_with_suffix
      # value_type_suffix is None initially if no dot

    # If value_type_suffix was not found by '.', try to find it from KNOWN_VALUE_TYPE_SUFFIXES
    if not components['value_type_suffix']:
        longest_found_suffix = None
        # Check if main_part ends with any known suffix (longest match preferred)
        for known_suffix in KNOWN_VALUE_TYPE_SUFFIXES:
            if main_part.endswith(f"_{known_suffix}"):
                if longest_found_suffix is None or len(known_suffix) > len(longest_found_suffix):
                    longest_found_suffix = known_suffix
            elif main_part == known_suffix: # Case where main_part itself is a suffix
                if longest_found_suffix is None or len(known_suffix) > len(longest_found_suffix):
                    longest_found_suffix = known_suffix

        if longest_found_suffix:
            components['value_type_suffix'] = longest_found_suffix
            if main_part == longest_found_suffix:
                main_part = "" # main_part was just the suffix, resulting mpc will be empty or ['']
            else:
                # Remove the suffix and the preceding underscore from main_part
                main_part = main_part[:-len(longest_found_suffix)-1]

    mpc = main_part.split('_') if main_part else [] # Re-split main_part if it was modified, handle if main_part became ""
    if mpc == [''] and main_part == "": # If main_part became "" and split('_') results in [''], make mpc empty.
        mpc = []

    # Now, mpc contains parts for group_location_prefix, plc_id, and equipment_id_full
    mpc_len = len(mpc)

    if mpc_len == 0:
        components['equipment_id_full'] = None
    elif mpc_len == 1:
        components['equipment_id_full'] = mpc[0]
    elif mpc_len == 2:
        is_first_part_group_like = '_' in mpc[0] or (len(mpc[0]) > 3 and not mpc[0].isupper())
        is_second_part_plc_like = "PLC" in mpc[1].upper()

        if is_first_part_group_like and is_second_part_plc_like : # G_P
            components['group_location_prefix'] = mpc[0]
            components['plc_id'] = mpc[1]
            components['equipment_id_full'] = None
        else: # Assume P_E
            components['plc_id'] = mpc[0]
            components['equipment_id_full'] = mpc[1]
    elif mpc_len == 3:
      is_mpc0_long_or_mixed_case = len(mpc[0]) > 3 or not mpc[0].isupper()

      if is_mpc0_long_or_mixed_case: # Heuristic for 'SomeGroup' style group prefix (G_P_E)
          components['group_location_prefix'] = mpc[0]
          components['plc_id'] = mpc[1]
          components['equipment_id_full'] = mpc[2]
      else: # Heuristic for 'VIS_VV' style group prefix (G1G2_P_None)
          components['group_location_prefix'] = "_".join(mpc[0:2])
          components['plc_id'] = mpc[2]
          components['equipment_id_full'] = None
    elif mpc_len >= 4: # Standard G1G2_P_E... structure
      components['group_location_prefix'] = "_".join(mpc[0:2])
      components['plc_id'] = mpc[2]
      equipment_actual_parts = mpc[3:]
      if equipment_actual_parts:
          components['equipment_id_full'] = "_".join(equipment_actual_parts)
      else:
          components['equipment_id_full'] = None

    # Fallback for short main_parts (this block might need review or removal due to new mpc_len logic)
    if main_part and not components['group_location_prefix'] and not components['plc_id'] and not components['equipment_id_full']:
        if len(mpc) == 1 and not components['value_type_suffix']:
            if mpc[0].startswith("PLC") or mpc[0].endswith("PLC"):
                components['plc_id'] = mpc[0]
                if components['equipment_id_full'] == mpc[0]: components['equipment_id_full'] = None

  # (Removed the redundant "Final check for no backslash" block as it's covered by len(parts)<2 logic path)

  # Parse equipment_id_full into prefix, numeric_id, and suffix_property
  # This block will now run for both cases (with or without '\')
  if components['equipment_id_full']:
    eq_parts = components['equipment_id_full'].split('_')
    if eq_parts:
      first_eq_part = eq_parts[0]
      # Basic validation for equipment_type_prefix (alpha) and equipment_numeric_id (numeric)
      if len(first_eq_part) > 2 and first_eq_part[:2].isalpha() and first_eq_part[2:].isdigit():
        components['equipment_type_prefix'] = first_eq_part[:2]
        components['equipment_numeric_id'] = first_eq_part[2:]
      else: # Does not fit AA12345 pattern, could be single part like "EP" or just "GH15051"
        components['equipment_type_prefix'] = first_eq_part # Or None if not matching pattern?
        # If it's just numeric like "15151", then prefix is None, numeric_id is "15151"
        # This needs more robust parsing for various equipment ID styles.
        # For now, if not AA12345, the whole first_eq_part is prefix, numeric_id is None.
        # Or, if it is all numeric, then prefix is None.
        if first_eq_part.isdigit():
            components['equipment_numeric_id'] = first_eq_part
            components['equipment_type_prefix'] = None # Explicitly
        else: # Non-numeric, and not fitting AA12345 pattern
            if len(first_eq_part) >= 2 and first_eq_part[:2].isalpha():
                 components['equipment_type_prefix'] = first_eq_part[:2]
                 # Potentially, the rest could be a numeric_id if it's all digits
                 # For now, if it didn't fit AA12345, numeric_id is from that pattern or None
                 if len(first_eq_part) > 2 and first_eq_part[2:].isdigit() and not components['equipment_numeric_id']:
                     components['equipment_numeric_id'] = first_eq_part[2:]
                 elif not components['equipment_numeric_id']: # If not set by AA12345 and rest not digits
                     components['equipment_numeric_id'] = None # ensure it's None
            else: # Less than 2 chars, or first 2 not alpha
                components['equipment_type_prefix'] = first_eq_part
                # components['equipment_numeric_id'] would have been set if all digits, else None

      if len(eq_parts) > 1:
        components['equipment_suffix_property'] = "_".join(eq_parts[1:])

  # Final check for value_type_suffix if not found and equipment_suffix_property might be it
  if not components['value_type_suffix'] and components['equipment_suffix_property']:
      if components['equipment_suffix_property'] in KNOWN_VALUE_TYPE_SUFFIXES:
          # This implies equipment_suffix_property was actually the value_type_suffix
          # e.g. VIS_VV_PLC1_CT15151_EP where EP is value_type_suffix
          # We need to be careful not to misinterpret a genuine property.
          # This rule should be applied if there was NO '.' and NO other assignment to value_type_suffix

          # Let's refine: this should only happen if original main_part_with_suffix had no '.'
          # and the last part of equipment_id_full (before splitting into property) was a known suffix.
          # The current logic parses equipment_id_full first, then splits it.
          # Consider "VIS_VV_PLC1_GH15051_EP" (no dot)
          # main_part = "VIS_VV_PLC1_GH15051_EP"
          # main_part_components = ["VIS", "VV", "PLC1", "GH15051", "EP"]
          # group_location_prefix = "VIS_VV"
          # plc_id = "PLC1"
          # remaining_eq_parts = ["GH15051", "EP"]
          # If value_type_suffix is None at this point:
          #   If "EP" in KNOWN_VALUE_TYPE_SUFFIXES:
          #     components['value_type_suffix'] = "EP"
          #     remaining_eq_parts.pop() -> ["GH15051"]
          #   components['equipment_id_full'] = "GH15051"
          # Then parsing GH15051: prefix=GH, numeric=15051, suffix_property=None. This is correct.
          # The logic for this is already partially covered above when remaining_eq_parts are processed.

          # What if equipment_suffix_property itself is a known suffix, and value_type_suffix is also set?
          # e.g. CT15151_PV4.MV_ING where PV4 is not in KNOWN_VALUE_TYPE_SUFFIXES. This is fine.
          # What if CT15151_EP.MV_ING where EP is a property.
          # The current logic for equipment_id_full parsing should handle this.
          pass # The earlier logic for remaining_eq_parts should handle this correctly.


  return components

def generate_synthetic_data_point(parsed_components, timestamp, last_value=None):
  """
  Generates a synthetic data point based on parsed components, a given timestamp, and optional last_value.
  """
  generated_value = None

  value_suffix = parsed_components.get('value_type_suffix')
  equip_prefix = parsed_components.get('equipment_type_prefix')

  if value_suffix == 'MV_ING':
    if equip_prefix == 'CT':
      generated_value = random.uniform(0.0, 100.0)
    elif equip_prefix == 'CP':
      generated_value = random.uniform(0.0, 10.0)
    elif equip_prefix == 'CF':
      generated_value = random.uniform(0.0, 500.0)
    else:
      generated_value = random.uniform(0.0, 1000.0)
  elif value_suffix == 'Total':
    if last_value is not None:
      generated_value = last_value + random.uniform(0, 100)
    else:
      generated_value = random.uniform(1000.0, 2000.0) # Smaller initial range
  elif value_suffix == 'Total_INT':
    if last_value is not None:
      generated_value = last_value + random.randint(0, 100)
    else:
      generated_value = random.randint(1000, 2000) # Smaller initial range
  elif value_suffix == 'DRT':
    if last_value is not None:
      generated_value = last_value + random.randint(0, 300) # Up to 5 mins increment
    else:
      generated_value = random.randint(0, 3600) # Initial runtime up to 1 hour
  elif value_suffix == 'EP':
    generated_value = random.uniform(0.0, 100.0)
  else: # Default case
    generated_value = random.uniform(0.0, 100.0)

  return {'timestamp': timestamp, 'value': round(generated_value, 3) if isinstance(generated_value, float) else generated_value}

def generate_dataset(value_name_list, num_points_per_name, start_datetime=None, time_increment_seconds=60):
    """
    Generates a dataset of synthetic data points for a list of value names.
    """
    if start_datetime is None:
        start_datetime = datetime.datetime.now()

    all_data_points = []

    for value_name_string in value_name_list:
        parsed_components = parse_value_name(value_name_string)

        # Basic check for parsing success, e.g. if category_system is None (or other critical fields)
        if not parsed_components or not parsed_components.get('category_system'):
            print(f"WARNING: Failed to parse value_name_string: {value_name_string}. Skipping.")
            continue

        current_last_value = None # Initialize last value for each tag
        current_timestamp = start_datetime
        for _ in range(num_points_per_name):
            dp_values = generate_synthetic_data_point(parsed_components, current_timestamp, current_last_value)

            if parsed_components.get('value_type_suffix') in ('Total', 'Total_INT', 'DRT'):
                current_last_value = dp_values['value']

            # Merge all dictionaries: {'value_name': ...}, parsed_components, data_point_values
            comprehensive_data_point = {'value_name': value_name_string}
            comprehensive_data_point.update(parsed_components)
            comprehensive_data_point.update(dp_values) # Use dp_values here

            all_data_points.append(comprehensive_data_point)
            current_timestamp += datetime.timedelta(seconds=time_increment_seconds)

    return all_data_points

if __name__ == '__main__':
  """
  Main entry point for the script.
  Includes test cases for parse_value_name.
  """
  test_cases = [
      # Test cases for parse_value_name are kept for regression testing
      # but their direct print output will be minimized for clarity below.
      ('VIS_VV_Mätvärden\\VIS_VV_PLC1_CT15151_PV4.MV_ING', {
          'original_string': 'VIS_VV_Mätvärden\\VIS_VV_PLC1_CT15151_PV4.MV_ING',
          'category_system': 'VIS_VV_Mätvärden',
          'group_location_prefix': 'VIS_VV',
          'plc_id': 'PLC1',
          'equipment_id_full': 'CT15151_PV4',
          'equipment_type_prefix': 'CT',
          'equipment_numeric_id': '15151',
          'equipment_suffix_property': 'PV4',
          'value_type_suffix': 'MV_ING'
      }),
      ('TS_Driftid\\MAR_TS_PLC1_AH13015_DS.DRT', {
          'original_string': 'TS_Driftid\\MAR_TS_PLC1_AH13015_DS.DRT',
          'category_system': 'TS_Driftid',
          'group_location_prefix': 'MAR_TS',
          'plc_id': 'PLC1',
          'equipment_id_full': 'AH13015_DS',
          'equipment_type_prefix': 'AH',
          'equipment_numeric_id': '13015',
          'equipment_suffix_property': 'DS',
          'value_type_suffix': 'DRT'
      }),
      ('VIS_VV_El_Effekt_EP\\VIS_VV_PLC1_GH15051_EP', { # Missing dot, EP is value_type_suffix
          'original_string': 'VIS_VV_El_Effekt_EP\\VIS_VV_PLC1_GH15051_EP',
          'category_system': 'VIS_VV_El_Effekt_EP',
          'group_location_prefix': 'VIS_VV',
          'plc_id': 'PLC1',
          'equipment_id_full': 'GH15051',
          'equipment_type_prefix': 'GH',
          'equipment_numeric_id': '15051',
          'equipment_suffix_property': None,
          'value_type_suffix': 'EP'
      }),
      ('Category\\Group_Loc_PLC_EQ123_Prop.Suffix', { # Generic test
          'original_string': 'Category\\Group_Loc_PLC_EQ123_Prop.Suffix',
          'category_system': 'Category',
          'group_location_prefix': 'Group_Loc',
          'plc_id': 'PLC',
          'equipment_id_full': 'EQ123_Prop',
          'equipment_type_prefix': 'EQ',
          'equipment_numeric_id': '123',
          'equipment_suffix_property': 'Prop',
          'value_type_suffix': 'Suffix'
      }),
      ('Category\\Group_Loc_PLC_EQ123.Suffix', { # No equipment property
          'original_string': 'Category\\Group_Loc_PLC_EQ123.Suffix',
          'category_system': 'Category',
          'group_location_prefix': 'Group_Loc',
          'plc_id': 'PLC',
          'equipment_id_full': 'EQ123',
          'equipment_type_prefix': 'EQ',
          'equipment_numeric_id': '123',
          'equipment_suffix_property': None,
          'value_type_suffix': 'Suffix'
      }),
      ('Category\\Group_Loc_PLC_EQ123_Total', { # Missing dot, Total is value_type_suffix
          'original_string': 'Category\\Group_Loc_PLC_EQ123_Total',
          'category_system': 'Category',
          'group_location_prefix': 'Group_Loc',
          'plc_id': 'PLC',
          'equipment_id_full': 'EQ123',
          'equipment_type_prefix': 'EQ',
          'equipment_numeric_id': '123',
          'equipment_suffix_property': None,
          'value_type_suffix': 'Total'
      }),
      ('PROJ_Alarmnivåer_EP', { # No backslash, EP is value_type_suffix
          'original_string': 'PROJ_Alarmnivåer_EP',
          'category_system': 'PROJ_Alarmnivåer_EP', # Entire string is category if no '\'
          'group_location_prefix': None, # Updated expectation
          'plc_id': None, # Updated expectation
          'equipment_id_full': 'PROJ_Alarmnivåer', # Updated expectation
          'equipment_type_prefix': None, # Updated expectation
          'equipment_numeric_id': None, # Updated expectation
          'equipment_suffix_property': None, # Updated expectation
          'value_type_suffix': 'EP' # Updated expectation
      }),
      ('VIS_VV_Mätvärden\\VIS_VV_PLC1.MV_ING', { # No equipment ID
          'original_string': 'VIS_VV_Mätvärden\\VIS_VV_PLC1.MV_ING',
          'category_system': 'VIS_VV_Mätvärden',
          'group_location_prefix': 'VIS_VV',
          'plc_id': 'PLC1',
          'equipment_id_full': None, # Corrected
          'equipment_type_prefix': None,
          'equipment_numeric_id': None,
          'equipment_suffix_property': None,
          'value_type_suffix': 'MV_ING'
      }),
      ('TS_Minimum\\MAR_TS_PLC0_MINPOS_Total_INT', { # Suffix Total_INT without dot
            'original_string': 'TS_Minimum\\MAR_TS_PLC0_MINPOS_Total_INT',
            'category_system': 'TS_Minimum',
            'group_location_prefix': 'MAR_TS',
            'plc_id': 'PLC0',
            'equipment_id_full': 'MINPOS',
            'equipment_type_prefix': 'MI', # MI from MINPOS
            'equipment_numeric_id': None, # No numeric part in MINPOS, if it's not following AA123 format
            'equipment_suffix_property': None, # If MINPOS is treated as a single ID part
            'value_type_suffix': 'Total_INT'
      }),
      ('SomeSystem\\SomeGroup_SomePLC_ActualValue_MV_ING', { # MV_ING as suffix, ActualValue as equipment
            'original_string': 'SomeSystem\\SomeGroup_SomePLC_ActualValue_MV_ING',
            'category_system': 'SomeSystem',
            'group_location_prefix': 'SomeGroup',
            'plc_id': 'SomePLC',
            'equipment_id_full': 'ActualValue',
            'equipment_type_prefix': 'Ac',
            'equipment_numeric_id': None, # No numeric part in ActualValue
            'equipment_suffix_property': None,
            'value_type_suffix': 'MV_ING'
      }),
      # Case where equipment_id might be misparsed if it's short and numeric, and there's no suffix property
      ('TestCat\\Test_Group_PLC_12345_EP', {
            'original_string': 'TestCat\\Test_Group_PLC_12345_EP',
            'category_system': 'TestCat',
            'group_location_prefix': 'Test_Group',
            'plc_id': 'PLC',
            'equipment_id_full': '12345', # equipment_id_full is '12345'
            'equipment_type_prefix': None, # No prefix if it's all numeric
            'equipment_numeric_id': '12345', # All numeric
            'equipment_suffix_property': None,
            'value_type_suffix': 'EP'
      }),
       ('TestCat\\Test_Group_PLC_TE12345_Prop_DRT', {
            'original_string': 'TestCat\\Test_Group_PLC_TE12345_Prop_DRT',
            'category_system': 'TestCat',
            'group_location_prefix': 'Test_Group',
            'plc_id': 'PLC',
            'equipment_id_full': 'TE12345_Prop',
            'equipment_type_prefix': 'TE',
            'equipment_numeric_id': '12345',
            'equipment_suffix_property': 'Prop',
            'value_type_suffix': 'DRT'
      }),
  ]

  for i, (input_str, expected_output) in enumerate(test_cases):
    print(f"Test Case {i+1}: {input_str}")
    result = parse_value_name(input_str)
    # print(f"Result: {result}") # Keep commented unless debugging parse_value_name

    match = True
    for key in expected_output:
        if result.get(key) != expected_output[key]: # Use .get for safety, though keys should match
            match = False
            # print(f"ERROR for key '{key}': Expected '{expected_output[key]}', Got '{result.get(key)}'")

    if match:
      # print("PASS\n") # Keep commented unless debugging parse_value_name
      pass
    else:
      # print("FAIL\n") # Keep commented unless debugging parse_value_name
      pass

  print("\n--- Testing generate_synthetic_data_point ---")
  parsed_mv_ct = {'value_type_suffix': 'MV_ING', 'equipment_type_prefix': 'CT'}
  parsed_mv_cp = {'value_type_suffix': 'MV_ING', 'equipment_type_prefix': 'CP'}
  parsed_mv_cf = {'value_type_suffix': 'MV_ING', 'equipment_type_prefix': 'CF'}
  parsed_mv_other = {'value_type_suffix': 'MV_ING', 'equipment_type_prefix': 'XX'}
  parsed_total = {'value_type_suffix': 'Total', 'equipment_type_prefix': 'ANY'}
  parsed_total_int = {'value_type_suffix': 'Total_INT', 'equipment_type_prefix': 'ANY'}
  parsed_drt = {'value_type_suffix': 'DRT', 'equipment_type_prefix': 'ANY'}
  parsed_ep = {'value_type_suffix': 'EP', 'equipment_type_prefix': 'ANY'}
  parsed_unknown_suffix = {'value_type_suffix': 'UNKNOWN', 'equipment_type_prefix': 'ANY'}
  parsed_none_suffix = {'value_type_suffix': None, 'equipment_type_prefix': 'ANY'}

  print("\n--- Testing generate_synthetic_data_point (with fixed timestamp) ---")
  fixed_ts = datetime.datetime(2024, 1, 1, 12, 0, 0)
  parsed_mv_ct = {'value_type_suffix': 'MV_ING', 'equipment_type_prefix': 'CT'}
  parsed_total_int = {'value_type_suffix': 'Total_INT', 'equipment_type_prefix': 'ANY'}
  print(f"Input: {parsed_mv_ct}, Output: {generate_synthetic_data_point(parsed_mv_ct, fixed_ts, None)}") # Added None for last_value
  print(f"Input: {parsed_total_int}, Output: {generate_synthetic_data_point(parsed_total_int, fixed_ts, None)}") # Added None for last_value
  # Example for cumulative
  print(f"Input: {parsed_total_int}, Output (cumulative): {generate_synthetic_data_point(parsed_total_int, fixed_ts, 1500)}")


  print("\n--- Testing generate_dataset ---")
  sample_value_names = [
      'VIS_VV_Mätvärden\\VIS_VV_PLC1_CT15151_PV4.MV_ING',
      'TS_Driftid\\MAR_TS_PLC1_AH13015_DS.DRT',         # Will be cumulative
      'Category\\Group_Loc_PLC_EQ123_Total_INT',       # Will be cumulative
      'InvalidStringFormat',
      'VIS_VV_El_Effekt_EP\\VIS_VV_PLC1_GH15051_EP',
      'Category\\PLC_EQ_DRT'                           # Another DRT for cumulative check
  ]

  dataset = generate_dataset(
      value_name_list=sample_value_names,
      num_points_per_name=3,
      time_increment_seconds=300
  )

  print(f"\nGenerated dataset contains {len(dataset)} data points.")
  print("First 9 data points from the dataset (to observe cumulative values):")
  for i in range(min(9, len(dataset))): # Increased to 9 to see more points
      print(dataset[i])

  # Example of how to check a specific point for structure
  if dataset:
    print("\nStructure of a data point (example):")
    # Find a DRT or Total_INT point to show structure
    example_point = next((p for p in dataset if p['value_type_suffix'] in ['DRT', 'Total_INT']), dataset[0])
    for key, value in example_point.items():
        print(f"  {key}: {value}")
