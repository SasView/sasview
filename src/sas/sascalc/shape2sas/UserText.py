from dataclasses import dataclass

@dataclass
class UserText:
    def __init__(self, imports: list[str], params: list[str], constraints: list[str], symbols: tuple[set[str], set[str]]):
        self.imports = imports
        self.params = params
        self.constraints = constraints
        self.symbols = symbols