from dataclasses import dataclass, field
from typing import TypeVar
from re import split as re_split
from metadata_filename_gui.metadata_tree_data import metadata as initial_metadata

T = TypeVar('T')


@dataclass
class InternalMetadataCategory[T]:
    values: dict[str, T] = field(default_factory=dict)

def default_categories() -> dict[str, InternalMetadataCategory[str | int]]:
    return {key: InternalMetadataCategory() for key in initial_metadata.keys()}

@dataclass
class InternalMetadata:
    # Key is the filename.
    filename_specific_metadata: dict[str, dict[str, InternalMetadataCategory[str]]] = field(default_factory=dict)
    filename_separator: dict[str, str] = field(default_factory=dict)
    master_metadata: dict[str, InternalMetadataCategory[int]] = field(default_factory=default_categories)

    def get_metadata(self, category: str, value: str, filename_components: list[str] = []) -> str:
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

    def update_metadata(self, category: str, key: str, filename: str, new_value: str | int):
        if isinstance(new_value, str):
            self.filename_specific_metadata[filename][category].values[key] = new_value
            # TODO: What about the master metadata? Until that's gone, that still takes precedence.
        elif isinstance(new_value, int):
            self.master_metadata[category].values[key] = new_value
        raise TypeError('Invalid type for new_value')

    def add_file(self, new_filename: str):
        # TODO: Fix typing here. Pyright is showing errors.
        self.filename_specific_metadata[new_filename] = default_categories()
