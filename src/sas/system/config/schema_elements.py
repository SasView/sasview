import logging
from abc import ABC, abstractmethod
from typing import Any

""" Type representation for config elements

Unfortunately, json schemas are not flexible enough to make this unnecessary"""

class SchemaError(Exception):
    """ Raised when there are problems creating a schema"""
    def __init__(self, message):
        super().__init__(message)

class CoercionError(Exception):
    """ Raised when we can't make a variable conform to the schema"""
    def __init__(self, message):
        self.message = message
        super().__init__(message)


class SchemaElement(ABC):
    """ Base class for schema elements"""
    @abstractmethod
    def coerce(self, value):
        """ Force a variable to conform to the schema, if possible"""
        pass

    def validate(self, value: Any) -> bool:
        """ Return true if value is valid according to the schema"""
        try:
            self.coerce(value)
            return True

        except CoercionError:
            return False

    def __eq__(self, value):
        return False


class SchemaVariable(SchemaElement):
    """ SchemaElement for values (i.e. float, int, bool, str)"""
    def __init__(self):
        pass

    schema_variable_type: str = ""

    def __eq__(self, other: SchemaElement):
        if isinstance(other, SchemaVariable):
            return self.schema_variable_type == other.schema_variable_type
        else:
            return False

    def __repr__(self):
        return f"Schema{self.schema_variable_type.capitalize()}"


class SchemaBool(SchemaVariable):
    schema_variable_type = "bool"

    def coerce(self, value):
        if isinstance(value, bool):
            return value
        else:
            raise CoercionError(f"Cannot coerce {type(value)} to bool")


class SchemaInt(SchemaVariable):
    schema_variable_type = "int"

    def coerce(self, value):
        if isinstance(value, int):
            return value
        else:
            raise CoercionError(f"Cannot coerce {type(value)} to int")


class SchemaFloat(SchemaVariable):
    schema_variable_type = "float"

    def coerce(self, value):
        if isinstance(value, (int, float)):
            return float(value)
        else:
            raise CoercionError(f"Cannot coerce {type(value)} to float")


class SchemaStr(SchemaVariable):
    schema_variable_type = "str"

    def coerce(self, value):
        return str(value)



class SchemaNonSpecified(SchemaElement):
    """ Representation of a list with elements of an unknown type -
    we use this when an empty list is in the config, or default is set to None"""

    def __init__(self):
        pass

    def coerce(self, value):
        return value

    def __eq__(self, other: SchemaElement):
        return isinstance(other, SchemaNonSpecified)

    def __repr__(self):
        return "SchemaNonSpecified"


class SchemaList(SchemaElement):
    """ Schema Element representing a homogeneous list"""
    def __init__(self, child_type: SchemaElement):
        self.child_type = child_type

    def coerce(self, value):
        # Only really need to check for list as this should be the only json object made, but let's make it more general
        if not isinstance(value, (tuple, set, list)):
            raise CoercionError(f"Cannot coerce {value} ({type(value)}) to list")

        if not isinstance(value, list):
            logger = logging.getLogger(self.__class__.__name__)
            logger.warning(f"Corercing variable of type {type(value)} to list ({value})")

        return [self.child_type.coerce(x) for x in value]

    def __eq__(self, other: SchemaElement):
        if isinstance(other, SchemaList):
            return self.child_type == other.child_type
        else:
            return False

    def __repr__(self):
        return f"SchemaList({repr(self.child_type)})"


def create_schema_element(name: str, value, recursion_depth: int=10) -> SchemaElement:
    """ Get an appropriate schema element for a specified config datum"""

    # Limits the depth of list config items
    if recursion_depth <= 0:
        raise SchemaError(f"Config element '{name}' is too nested, or is self-referential")

    if value is None:
        logger = logging.getLogger("create_schema_element")
        logger.warning(f"Non-specified type for variable '{name}'")
        return SchemaNonSpecified()

    # List case
    elif isinstance(value, list):

        # Empty list
        if len(value) == 0:
            logger = logging.getLogger("create_schema_element")
            logger.warning(f"Non-specified list type for variable '{name}'")
            return SchemaList(SchemaNonSpecified())

        elif len(value) == 1:
            return SchemaList(create_schema_element(name, value[0], recursion_depth-1))

        else:
            schema_children = [create_schema_element(name, x, recursion_depth-1) for x in value]

            union_type = schema_union(schema_children)

            if union_type is None:
                # No homogeneous type possible
                raise SchemaError(f"Config does not support inhomogeneous lists, '{name}' has types {schema_children}")
            else:
                return SchemaList(union_type)

    # Not a list
    elif isinstance(value, bool):
        return SchemaBool()

    elif isinstance(value, int):
        return SchemaInt()

    elif isinstance(value, float):
        return SchemaFloat()

    elif isinstance(value, str):
        return SchemaStr()

    else:
        raise SchemaError(f"Config element is not a bool, int, float, str, or a homogeneous list thereof ({name}={value})")


def schema_union(elements: list[SchemaElement]):
    """ Union of an arbitrary number of Schema Elements"""
    if len(elements) == 0:
        return SchemaNonSpecified()

    elif len(elements) == 1:
        return elements[0]

    else:
        unioned = elements[0]
        for element in elements[1:]:
            unioned = pairwise_schema_union(unioned, element)
        return unioned


def pairwise_schema_union(a: SchemaElement | None, b: SchemaElement | None) -> SchemaElement | None:
    """ Pairwise union of Schema Elements"""

    if a is None or b is None:
        return None

    # Union of list types should be list of union type
    if isinstance(a, SchemaList) and isinstance(b, SchemaList):
        type_parameter = pairwise_schema_union(a.child_type, b.child_type)
        if type_parameter is None:
            return None
        else:
            return SchemaList(type_parameter)

    # Different types don't union, except for float and int
    if isinstance(a, SchemaVariable) and isinstance(b, SchemaVariable):

        if a.schema_variable_type == "int" and b.schema_variable_type == "float":
            return SchemaFloat()

        elif b.schema_variable_type == "int" and a.schema_variable_type == "float":
            return SchemaFloat()

        elif a == b:
            return a

        else:
            return None

    # Union of non specified with anything else is whatever that other thing is
    if isinstance(a, SchemaNonSpecified):
        return b

    if isinstance(b, SchemaNonSpecified):
        return a

    # All other combinations have no union type
    return None

