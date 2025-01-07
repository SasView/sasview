class MyClass:
    def f1(self):
        return "Function f1"

    def f2(self):
        return "Function f2"

def get_name():
    return "f1"  # This is just an example, it could be any logic to get the function name

# Create an instance of the class
obj = MyClass()

# Get the function name
name = get_name()

# Call the function using the name
if hasattr(obj, name):
    value = getattr(obj, name)()
    print(value)  # Output: Function f1
else:
    print("Function not found")


#Get position of Enum member
from enum import Enum

class Color(Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"

# Convert Enum members to a list
color_list = list(Color)

# Get the position of an Enum member
def get_position(color):
    return color_list.index(color)

# Example usage
print(get_position(Color.GREEN))  # Output: 1
print(get_position(Color.BLUE))   # Output: 2