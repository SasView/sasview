
""" Unit tests for Config system. """

import json
import unittest
from io import StringIO

import sas
import sas.system.version
from sas.system.config.config import Config
from sas.system.config.config_meta import MalformedFile
from sas.system.config.schema_elements import (
    CoercionError,
    SchemaBool,
    SchemaFloat,
    SchemaInt,
    SchemaList,
    SchemaNonSpecified,
    SchemaStr,
    create_schema_element,
    pairwise_schema_union,
)


class TestConfig(unittest.TestCase):

    def a_test_dict(self) -> dict:
        """ A dictionary with field names from the config, but with different values"""

        config = Config()

        # config variables (exclude the ones used by the base class)
        all_variables = vars(config).copy()
        for skipped in config._meta_attributes:
            del all_variables[skipped]

        string_value_suffix = 42

        target_values = {}

        for key in all_variables:

            if isinstance(all_variables[key], bool):
                target_values[key] = not all_variables[key]


            elif isinstance(all_variables[key], int):
                target_values[key] = all_variables[key] + 42

            elif isinstance(all_variables[key], float):
                target_values[key] = all_variables[key] + 3.149999

            elif isinstance(all_variables[key], str):
                target_values[key] = all_variables[key] + f" with string making it end in the number {string_value_suffix}"
                string_value_suffix += 1

            elif all_variables[key] == []:
                target_values[key] = ["something else"]

            elif isinstance(all_variables[key], list):
                target_values[key] = all_variables[key] * 2

            elif all_variables[key] is None:
                target_values[key] = "something"

            else:
                raise TypeError(f"Config entry '{key}' is not bool, int, float, str ({all_variables[key]})")

        return target_values

    def test_valid_update(self):
        """ Test setting variables with known valid options"""

        config = Config()
        test_dict = self.a_test_dict()

        config.update(test_dict)

        for key in test_dict:
            var = getattr(config, key)
            self.assertEqual(var, test_dict[key])
            self.assertEqual(type(var), type(test_dict[key]))


    def test_invalid_update_bad_name(self):
        """ Check that a warning is logged when there is a bad name in the config"""

        config = Config()

        # Create a variable that isn't in the config
        test_dict = self.a_test_dict()

        name = "x"
        while name in test_dict:
            name += "x"

        # try and set it
        with self.assertLogs('sas.config', level="WARNING") as cm:
            config.update({name: None})
            self.assertTrue(cm.output[0].startswith("WARNING:sas.config:"))

    def test_invalid_update_bad_type(self):

        """Check that bad types give an error, this tries a bunch of incompatable types with each of the
        existing entries in config

        For this test to be useful it requires config to have at least one default entry with a schematisable type
        """

        config = Config()
        test_dict = self.a_test_dict()
        for key in test_dict:

            # find types that should be incompatable
            for test_value in [False, 0, 1.0, "string", [1,2,3], [[["deep"]]]]:
                test_value_schema = create_schema_element("value not important", test_value)

                try:
                    config._schema[key].coerce(test_value)

                except CoercionError:

                    # Only test the ones that fail, i.e. cannot be coerced
                    if pairwise_schema_union(test_value_schema, config._schema[key]) is None:
                        with self.assertLogs('sas.config', level="ERROR") as cm:

                            # Try the bad value
                            config.update({key: test_value})

                            self.assertTrue(cm.output[0].startswith("ERROR:sas.config:"))


    def test_save_basics(self):
        file = StringIO()

        # Check saving with no changes, should be empty and
        config = Config()
        config.save_to_file_object(file)

        file.seek(0)

        observed = json.load(file)

        empty_file = {
            "sasview_version": sas.system.version.__version__,
             "config_data": {}
        }

        self.assertEqual(observed, empty_file)



    def test_save_changes(self):
        """ Check that save saves a change that has been made"""

        test_dict = self.a_test_dict()
        for key in test_dict:
            file = StringIO()
            config = Config()
            config.update({key: test_dict[key]})
            config.save_to_file_object(file)
            file.seek(0)

            observed = json.load(file)

            expected = {
                "sasview_version": sas.system.version.__version__,
                "config_data": {key: test_dict[key]}
            }

            self.assertEqual(observed, expected)

    def test_only_save_actual_changes(self):
        """ Check that if a field is set back to its default, it isn't saved in the config"""

        # (1) make a single change
        # (2) change back to the default value
        # (3) Check

        empty_file = {
            "sasview_version": sas.system.version.__version__,
             "config_data": {}
        }

        backup = Config()

        test_dict = self.a_test_dict()
        for key in test_dict:
            file = StringIO()
            config = Config()

            config.update({key: test_dict[key]})
            config.update({key: getattr(backup, key)})
            config.save_to_file_object(file)

            file.seek(0)
            observed = json.load(file)

            self.assertEqual(observed, empty_file)


    def test_bad_config_version(self):

        config = Config()
        file = StringIO()

        json.dump({
            "sasview_version": "1.2.3",
             "config_data": {}},
            file)

        file.seek(0)

        with self.assertLogs('sas.config', level="WARN") as cm:
            # Try the bad value
            config.load_from_file_object(file)

            self.assertTrue(cm.output[0].startswith("WARNING:sas.config:"))

    def test_bad_config_file_structure(self):

        config = Config()

        bad_structures = [
            {
                "sasview_version": sas.system.version.__version__,
                "quanfig_data": {}
            },
            {
                "sasview_version": "bad version",
                "config_data": {}
            },
            {
                "sassy_verberry": sas.system.version.__version__,
                "config_data": {}
            },
            {
                "sasview_version": sas.system.version.__version__,
                "config_data": []
            },
            {}
        ]

        for structure in bad_structures:
            file = StringIO()

            json.dump(structure,file)

            file.seek(0)

            with self.assertRaises(MalformedFile):
                config.load_from_file_object(file)


    def test_schema_union(self):
        """ Check the typing behaviour of the schema system"""

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


if __name__ == '__main__':
    unittest.main()
