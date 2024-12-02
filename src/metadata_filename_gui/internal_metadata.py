from dataclasses import dataclass
from typing import TypeVar
from re import split as re_split

T = TypeVar('T')


@dataclass
class InternalMetadataCategory[T]:
    values: dict[str, T]

@dataclass
class InternalMetadata:
    # Key is the filename.
    filename_specific_metadata: dict[str, dict[str, InternalMetadataCategory[str]]]
    master_metadata: dict[str, InternalMetadataCategory[int]]

    def get_metadata(self, category: str, value: str, filename: str, separator_pattern: str) -> str:
        filename_components = re_split(filename, separator_pattern)
        # We prioritise the master metadata.

        # TODO: Assumes category in master_metadata exists. Is this a reasonable assumption? May need to make sure it is
        # definitely in the dictionary.
        if value in self.master_metadata[category].values:
            index = self.master_metadata[category].values[value]
            return filename_components[index]
        target_category = self.filename_specific_metadata[filename][category].values
        if value in target_category:
            return target_category[value]
        raise ValueError('value does not exist in metadata.')
