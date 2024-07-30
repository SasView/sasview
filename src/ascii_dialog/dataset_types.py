""" Information used for providing guesses about what text based files contain """

from dataclasses import dataclass

#
#   VERY ROUGH DRAFT - FOR PROTOTYPING PURPOSES
#

@dataclass
class DatasetType:
    name: str
    required: list[str]
    optional: list[str]
    expected_orders: list[list[str]]


one_dim = DatasetType(
            name="1D I vs Q",
            required=["Q", "I"],
            optional=["dI", "dQ", "shadow"],
            expected_orders=[
                ["Q", "I", "dI"],
                ["Q", "dQ", "I", "dI"]])

two_dim = DatasetType(
            name="2D I vs Q",
            required=["Qx", "Qy", "I"],
            optional=["dQx", "dQy", "dI", "Qz", "shadow"],
            expected_orders=[
                ["Qx", "Qy", "I"],
                ["Qx", "Qy", "I", "dI"],
                ["Qx", "Qy", "dQx", "dQy", "I", "dI"]])

sesans = DatasetType(
    name="SESANS",
    required=["z", "G"],
    optional=["stuff", "other stuff", "more stuff"],
    expected_orders=[["z", "G"]])

dataset_types = {dataset.name for dataset in [one_dim, two_dim, sesans]}


#
# Some default units, this is not how they should be represented, some might not be correct
#
# The unit options should only be those compatible with the field
#
default_units = {
    "Q": "1/A",
    "I": "1/cm",
    "Qx": "1/A",
    "Qy": "1/A",
    "Qz": "1/A",
    "dI": "1/A",
    "dQ": "1/A",
    "dQx": "1/A",
    "dQy": "1/A",
    "dQz": "1/A",
    "z": "A",
    "G": "<none>",
    "shaddow": "<none>",
    "temperature": "K",
    "magnetic field": "T"
}

#
# Other possible fields. Ultimately, these should come out of the metadata structure
#

metadata_fields = [
    "temperature",
    "magnetic field",
]
