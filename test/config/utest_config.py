
import unittest
from sas import config
from sas.config_system.schema_elements import \
    pairwise_schema_union, \
    SchemaBool, SchemaInt, SchemaFloat, SchemaStr, \
    SchemaList, SchemaNonSpecified

""" Unit tests for Config system. """


class TestConfig(unittest.TestCase):

    def a_test_dict(self) -> dict:
        """ A dictionary with field names from the config, but with different values"""

        # config variables (exclude the ones used by the base class)
        all_variables = vars(config).copy()
        del all_variables["_locked"]
        del all_variables["_schema"]
        del all_variables["_modified_values"]


        # New values
        bool_value = True
        int_value = 42
        float_value = 2.7669
        string_value_suffix = 7

        target_values = {}

        for key in all_variables:

            if isinstance(all_variables[key], bool):
                target_values[key] = bool_value
                bool_value = not bool_value


            elif isinstance(all_variables[key], int):
                target_values[key] = int_value
                int_value += 1

            elif isinstance(all_variables[key], float):
                target_values[key] = int_value
                float_value += 3.149999

            elif isinstance(all_variables[key], str):
                target_values[key] = f"A string ending in the number {string_value_suffix}"
                string_value_suffix += 1

            elif isinstance(all_variables[key], list):
                target_values[key] = all_variables[key] * 2 # Finding a more specific test is too complicated

            elif all_variables[key] is None:
                target_values[key] = None

            else:
                raise TypeError(f"Config entry '{key}' is not bool, int, float, str ({all_variables[key]})")

        return target_values

    def test_valid_update(self):
        """ Test setting variables with known valid options"""

        test_dict = self.a_test_dict()

        config.update(test_dict)

        for key in test_dict:
            var = getattr(config, key)
            self.assertEqual(var, test_dict[key])
            self.assertEqual(type(var), type(test_dict[key]))

    def test_config_variable_change_tracker(self):
        pass

    def test_invalid_update_bad_name(self):
        pass

    def test_invalid_update_bad_type(self):
        pass

    def test_load_and_save(self):
        pass

    def test_schema_union(self):

        anything = SchemaNonSpecified()

        boolean = SchemaBool()
        integer = SchemaInt()
        floating = SchemaFloat()
        string = SchemaStr()

        empty_list = SchemaList(anything)
        bool_list = SchemaList(boolean)
        int_list = SchemaList(integer)
        float_list = SchemaList(floating)
        str_list = SchemaList(string)

        empty_list2 = SchemaList(empty_list)
        bool_list2 = SchemaList(bool_list)
        int_list2 = SchemaList(int_list)
        float_list2 = SchemaList(float_list)
        str_list2 = SchemaList(str_list)

        all_base = [anything, boolean, integer, floating, string]
        all_level_1 = [empty_list, bool_list, int_list, float_list, str_list]
        all_level_2 = [empty_list2, bool_list2, int_list2, float_list2, str_list2]

        #
        # Unspecified
        #
        for x in all_base + all_level_1 + all_level_2:
            self.assertEqual(pairwise_schema_union(x, anything), x)
            self.assertEqual(pairwise_schema_union(anything, x), x)

        #
        # Variable classes
        #

        # Incompatible cases

        self.assertIsNone(pairwise_schema_union(integer, string))
        self.assertIsNone(pairwise_schema_union(integer, boolean))
        self.assertIsNone(pairwise_schema_union(string, integer))
        self.assertIsNone(pairwise_schema_union(boolean, integer))

        self.assertIsNone(pairwise_schema_union(floating, string))
        self.assertIsNone(pairwise_schema_union(floating, boolean))
        self.assertIsNone(pairwise_schema_union(string, floating))
        self.assertIsNone(pairwise_schema_union(boolean, floating))

        # Compatible cases
        self.assertEqual(pairwise_schema_union(floating, integer), floating)
        self.assertEqual(pairwise_schema_union(integer, floating), floating)

        #
        # Lists - a few important cases
        #

        # lists of non-compatible types should not be combined
        self.assertIsNone(pairwise_schema_union(str_list, int_list))
        self.assertIsNone(pairwise_schema_union(str_list, bool_list))
        self.assertIsNone(pairwise_schema_union(int_list, str_list))
        self.assertIsNone(pairwise_schema_union(bool_list, str_list))

        # Lists of the same kind but with different nesting should not combine
        self.assertIsNone(pairwise_schema_union(str_list, str_list2))
        self.assertIsNone(pairwise_schema_union(str_list2, str_list))

        # empty list should not care about level
        self.assertEqual(pairwise_schema_union(empty_list, str_list), str_list)
        self.assertEqual(pairwise_schema_union(empty_list, str_list2), str_list2)
        self.assertEqual(pairwise_schema_union(str_list, empty_list), str_list)
        self.assertEqual(pairwise_schema_union(str_list2, empty_list), str_list2)

        # lists of floats and ints should combine to float
        self.assertEqual(pairwise_schema_union(float_list, int_list), float_list)
        self.assertEqual(pairwise_schema_union(float_list2, int_list2), float_list2)
        self.assertEqual(pairwise_schema_union(int_list, float_list), float_list)
        self.assertEqual(pairwise_schema_union(int_list2, float_list2), float_list2)

        #... but only at the same level
        self.assertIsNone(pairwise_schema_union(float_list2, int_list))
        self.assertIsNone(pairwise_schema_union(float_list, int_list2))
        self.assertIsNone(pairwise_schema_union(int_list2, float_list))
        self.assertIsNone(pairwise_schema_union(int_list, float_list2))


    def test_schema_extraction(self):
        pass


if __name__ == '__main__':
    unittest.main()
