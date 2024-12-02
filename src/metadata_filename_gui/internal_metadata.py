from dataclasses import dataclass
from typing import TypeVar

T = TypeVar('T')


@dataclass
class InternalMetadataCategory[T]:
    values: dict[str, T]

@dataclass
class InternalMetadata:
    # Key is the filename.
    filename_specific_metadata: dict[str, InternalMetadataCategory[str]]
    master_metadata: dict[str, InternalMetadataCategory[int]]
