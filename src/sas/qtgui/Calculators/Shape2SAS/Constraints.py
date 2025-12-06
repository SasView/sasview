#Global
import ast
import importlib.util
import logging
import traceback

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton, QWidget

from sas.qtgui.Calculators.Shape2SAS.ButtonOptions import ButtonOptions
from sas.qtgui.Calculators.Shape2SAS.Tables.variableTable import VariableTable
from sas.qtgui.Calculators.Shape2SAS.UI.ConstraintsUI import Ui_Constraints
from sas.qtgui.Utilities.ModelEditors.TabbedEditor.ModelEditor import ModelEditor
from sas.sascalc.shape2sas.UserText import UserText

logger = logging.getLogger(__name__)

VAL_TYPE = str | int | float


class Constraints(QWidget, Ui_Constraints):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        #Setup GUI for Constraints
        self.constraintTextEditor = ModelEditor() #SasView's standard text editor
        self.constraintTextEditor.modelModified.connect(lambda: self.createPlugin.setEnabled(True))
        self.constraintTextEditor.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.constraintTextEditor.gridLayout_16.setContentsMargins(5, 5, 5, 5)
        self.constraintTextEditor.groupBox_13.setTitle("Constraints") #override title
        self.verticalLayout.insertWidget(0, self.constraintTextEditor)
        self.variableTable = VariableTable()
        self.buttonOptions = ButtonOptions()
        self.buttonOptions.help.setToolTip("Go to help page")
        self.buttonOptions.closePage.setToolTip("Close Shape2SAS")
        self.buttonOptions.reset.setToolTip("Reset this page to default")

        self.gridLayout_2.addWidget(self.variableTable, 0, 1, 1, 1)
        self.gridLayout_2.addWidget(self.buttonOptions, 1, 0, 1, 0, Qt.AlignmentFlag.AlignRight)

        self.createPlugin = QPushButton("Create Plugin")
        self.createPlugin.setMinimumSize(110, 24)
        self.createPlugin.setMaximumSize(110, 24)
        self.createPlugin.setToolTip("Create the plugin model. It will be available in the Plugin Models category in the Fit panel.")
        self.createPlugin.setEnabled(False)
        self.variableTable.on_item_changed_callback = lambda _: self.createPlugin.setEnabled(True)

        self.buttonOptions.horizontalLayout_5.insertWidget(1, self.createPlugin)
        self.buttonOptions.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)

        #Setup default logbook text
        defaultText = "<span><b>Shape2SAS plugin constraints log</b></p></span>"
        self.textEdit_2.append(defaultText)

    def log_embedded_error(self, message: str):
        """Log an error message in the embedded logbook."""
        self.textEdit_2.append(f"<span style='color: red;'>{message}</span>")
        self.textEdit_2.verticalScrollBar().setValue(self.textEdit_2.verticalScrollBar().maximum())
        logger.error(message)

    def log_embedded(self, message: str):
        """Log a message in the embedded logbook."""
        self.textEdit_2.append(f"<span style='color: black;'>{message}</span>")
        self.textEdit_2.verticalScrollBar().setValue(self.textEdit_2.verticalScrollBar().maximum())

    def getConstraintText(self, fit_params: str) -> str:
        """Get the default text for the constraints editor"""

        self.constraintText = (
            "# Write libraries to be imported here.\n"
            "from numpy import inf\n"
            "\n"
            "# Modify fit parameters here.\n"
            f"parameters = {fit_params}\n"
            "\n"
            "# Define your constraints here.\n"
            "# Both absolute and relative parameters can be used.\n"
            "# Example: dCOMX2 = dCOMX1 will make COMX2 track changes in COMX1\n"
        )

        return self.constraintText

    def setConstraints(self, parameter_text: str):
        """Insert the text into the constraints editor"""

        def get_default(parameter_text: str):
            return self.getConstraintText(parameter_text)

        def merge_text(current_text: str, parameter_text: str):
            if not current_text:
                return get_default(parameter_text)

            # search for 'parameters =' in the current text
            found = False
            current_text_lines = current_text.splitlines()
            for start, line in enumerate(current_text_lines):
                if line.startswith("parameters ="):
                    break

            # find closing bracket of the parameters list
            bracket_count = 0
            for end, line in enumerate(current_text_lines[start:]):
                bracket_count += line.count('[') - line.count(']')
                if bracket_count == 0:
                    # found the closing bracket
                    found = True
                    old_lines = current_text_lines[start:start+end+1]
                    break

            if not found:
                return get_default(parameter_text)

            new_lines = parameter_text.split("\n")
            # fit_param string is formatted as:
            # [
            #  # header
            #  ['name1', 'unit1', ...],
            #  ['name2', 'unit2', ...],
            # ...
            # ]
            # extract names from the first element of each sublist, skipping the first two and last lines
            table = str.maketrans("", "", "[]' ")
            old_names = [line.translate(table).split(",")[0] for line in old_lines[2:-1]]
            new_names = [line.translate(table).split(",")[0] for line in new_lines[2:-1]]

            # create new list of parameters, replacing existing old lines in the new list
            for i, name in enumerate(new_names):
                if name in old_names:
                    entry = old_lines[old_names.index(name)+2]
                    new_lines[i+2] = entry + ',' if entry[-1] != ',' else entry

            # remove old lines from the current text and insert the new ones in the middle
            current_text = "\n".join(current_text_lines[:start+1] + new_lines[2:-1] + current_text_lines[start+end:])
            return current_text

        current_text = self.constraintTextEditor.txtEditor.toPlainText()
        text = merge_text(current_text, parameter_text)
        self.constraintTextEditor.txtEditor.setPlainText(text)
        self.createPlugin.setEnabled(True)

    def parseConstraintsText(self,
        text: str, fitPar: list[str], modelPars: list[list[str]], modelVals: list[list[float]], checkedPars: list[list[bool]]
    ) -> tuple[list[str], str, str, list[list[bool]]]:
        """Parse the text in the constraints editor and return a dictionary of parameters"""

        logger.debug("Parsing constraints text.")
        logger.debug("Received input:")
        logger.debug(f"fitPar: {fitPar}")
        logger.debug(f"modelPars: {modelPars}")
        logger.debug(f"modelVals: {modelVals}")
        logger.debug(f"checkedPars: {checkedPars}")

        def as_ast(text: str):
            try:
                return ast.parse(text)
            except SyntaxError as e:
                # log most recent traceback error
                all_lines = traceback.format_exc().split('\n')
                last_lines = all_lines[-1:]
                traceback_to_show = '\n'.join(last_lines)
                logger.error(traceback_to_show)
                self.log_embedded_error(f"{e}")
                return None

        def expand_center_of_mass_pars(constraint: ast.Assign) -> list[ast.Assign]:
            """Expand center of mass parameters to include all components."""

            # check if this is a COM assignment we need to expand
            if (len(constraint.targets) != 1 or
                not isinstance(constraint.targets[0], ast.Name) or
                not isinstance(constraint.value, ast.Name)):
                return constraint

            lhs = constraint.targets[0].id
            rhs = constraint.value.id

            # check if lhs is a COM parameter (with or without 'd' prefix)
            lhs_is_delta = lhs.startswith('d')
            lhs_base = lhs[1:] if lhs_is_delta else lhs

            if not (lhs_base.startswith("COM") and lhs_base[3:].isdigit()):
                return constraint

            # check rhs
            rhs_is_delta = rhs.startswith('d')
            rhs_base = rhs[1:] if rhs_is_delta else rhs

            new_targets, new_values = [], []
            if rhs_base.startswith("COM") and rhs_base[3:].isdigit():
                # rhs is also a COM parameter: COM2 = COM1 -> COMX2, COMY2, COMZ2 =COMX1, COMY1, COMZ1
                lhs_shape_num = lhs_base[3:]
                rhs_shape_num = rhs_base[3:]

                for axis in ['X', 'Y', 'Z']:
                    lhs_full = f"{'d' if lhs_is_delta else ''}COM{axis}{lhs_shape_num}"
                    rhs_full = f"{'d' if rhs_is_delta else ''}COM{axis}{rhs_shape_num}"
                    new_targets.append(ast.Name(id=lhs_full, ctx=ast.Store()))
                    new_values.append(ast.Name(id=rhs_full, ctx=ast.Load()))

            else:
                # rhs is a regular parameter: COM2 = X -> COMX2, COMY2, COMZ2 = X, X, X
                lhs_shape_num = lhs_base[3:]
                rhs_full = f"{'d' if rhs_is_delta else ''}{rhs_base}"
                for axis in ['X', 'Y', 'Z']:
                    lhs_full = f"{'d' if lhs_is_delta else ''}COM{axis}{lhs_shape_num}"
                    new_targets.append(ast.Name(id=lhs_full, ctx=ast.Store()))
                    new_values.append(ast.Name(id=rhs_full, ctx=ast.Load()))

            constraint.targets = [ast.Tuple(elts=new_targets, ctx=ast.Store())]
            constraint.value = ast.Tuple(elts=new_values, ctx=ast.Load())
            return constraint

        def parse_ast(tree: ast.AST):
            params = None
            imports = []
            constraints = []

            for node in ast.walk(tree):
                match node:
                    case ast.ImportFrom() | ast.Import():
                        imports.append(node)

                    case ast.Assign():
                        if len(node.targets) != 1 or isinstance(node.targets[0], ast.Tuple) or isinstance(node.value, ast.Tuple):
                            self.log_embedded_error(f"Tuple assignment is not supported (line {node.lineno}).")
                            raise ValueError(f"Tuple assignment is not supported (line {node.lineno}).")

                        if node.targets[0].id == 'parameters':
                            params = node
                            continue

                        if node.targets[0].id.startswith('dCOM') or node.targets[0].id.startswith('COM'):
                            constraints.append(expand_center_of_mass_pars(node))
                        else:
                            constraints.append(node)
            return params, imports, constraints

        def extract_symbols(constraints: list[ast.AST]) -> tuple[list[str], list[str]]:
            """Extract all symbols used in the constraints."""
            lhs, rhs = set(), set()
            lineno = {}

            # Helper function to discover named parameters in the supplied AST, adding them to the provided set.
            def discover_params(param: ast.AST, add_to_set: set[str]):
                match param:
                    case ast.Name():
                        add_to_set.add(param.id)
                        lineno[param.id] = param.lineno
                    case ast.Tuple():
                        for elt in param.elts:
                            if isinstance(elt, ast.Name):
                                add_to_set.add(elt.id)
                                lineno[elt.id] = elt.lineno

            for node in constraints:
                for target in node.targets:
                    discover_params(target, lhs)

                for value in ast.walk(node.value):
                    discover_params(value, rhs)

            return lhs, rhs, lineno

        def validate_params(params: ast.AST):
            if params is None:
                self.log_embedded_error("No parameters found in constraints text.")
                raise ValueError("No parameters found in constraints text.")

        def validate_symbols(lhs: list[str], rhs: list[str], symbol_linenos: dict[str, int], fitPars: list[str]):
            """Check if all symbols in lhs and rhs are valid parameters."""
            # lhs is not allowed to contain fit parameters
            for symbol in lhs:
                if symbol in fitPars or symbol[1:] in fitPars:
                    self.log_embedded_error(f"Symbol '{symbol}' is a fit parameter and cannot be assigned to (line {symbol_linenos[symbol]}).")
                    raise ValueError(f"Symbol '{symbol}' is a fit parameter and cannot be assigned to (line {symbol_linenos[symbol]}).")

            for symbol in rhs:
                is_fit_par = symbol in fitPars or symbol[1:] in fitPars
                is_defined = symbol in lhs
                if not is_fit_par and not is_defined:
                    self.log_embedded_error(f"Symbol '{symbol}' is undefined (line {symbol_linenos[symbol]}).")
                    raise ValueError(f"Symbol '{symbol}' is undefined (line {symbol_linenos[symbol]}).")

        def validate_imports(imports: list[ast.ImportFrom | ast.Import]):
            """Check if all imports are valid."""
            for imp in imports:
                if isinstance(imp, ast.ImportFrom):
                    if not importlib.util.find_spec(imp.module):
                        self.log_embedded_error(f"Module '{imp.module}' not found (line {imp.lineno}).")
                        raise ModuleNotFoundError(f"No module named {imp.module}")
                elif isinstance(imp, ast.Import):
                    for name in imp.names:
                        if not importlib.util.find_spec(name.name):
                            self.log_embedded_error(f"Module '{name.name}' not found (line {imp.lineno}).")
                            raise ModuleNotFoundError(f"No module named {name.name}")

        def mark_named_parameters(checkedPars: list[list[bool]], modelPars: list[str], symbols: set[str]):
            """Mark parameters in the modelPars as checked if they are in symbols_lhs."""
            def in_symbols(par: str):
                if par in symbols: return True
                if 'd' + par in symbols: return True
                return False

            for i, shape in enumerate(modelPars):
                for j, par in enumerate(shape):
                    if par is None:
                        continue
                    checkedPars[i][j] = checkedPars[i][j] or in_symbols(par)
            return checkedPars

        tree = as_ast(text)
        params, imports, constraints = parse_ast(tree)
        lhs, rhs, symbol_linenos = extract_symbols(constraints)
        validate_params(params)
        validate_symbols(lhs, rhs, symbol_linenos, fitPar)
        validate_imports(imports)

        params = ast.unparse(params)
        imports = [ast.unparse(imp) for imp in imports]
        constraints = [ast.unparse(constraint) for constraint in constraints]
        symbols = (lhs, rhs)

        self.log_embedded("Successfully parsed user text. Generating plugin model...")
        logger.debug(f"Parsed parameters: {params}")
        logger.debug(f"Parsed imports: {imports}")
        logger.debug(f"Parsed constraints: {constraints}")
        logger.debug(f"Symbols used: {symbols}")

        return UserText(imports, params, constraints, symbols), mark_named_parameters(checkedPars, modelPars, lhs.union(rhs))

    @staticmethod
    def getPosition(item: VAL_TYPE, itemLists: list[list[VAL_TYPE]]) -> tuple[int, int]:
        """Find position of an item in lists"""

        for i, sublist in enumerate(itemLists):
            if item in sublist:
                return i, sublist.index(item)

    @staticmethod
    def removeFromList(listItems: list[VAL_TYPE], listToCompare: list[VAL_TYPE]):
        """Remove items from a list if in another list"""

        finalpars = []
        for item in listItems:
            for statement in listToCompare:
                if item not in statement:
                    #NOTE: library names, "from" and "import" will also be removeds
                    finalpars.append(item)
        # Explicilty modify list sent to the method
        listItems = finalpars

    def ifParameterExists(self, lineNames: list[str], modelPars: list[list[str]]) -> bool:
        """Check if parameter exists in model parameters"""

        for par in lineNames:
            boolPar = any(par in sublist for sublist in modelPars)
            if not boolPar:
                logger.error(f"{par} does not exist in parameter table")

        return False

    def clearConstraints(self):
        """Clear text editor containing constraints"""
        self.constraintTextEditor.txtEditor.clear()
        self.textEdit_2.clear()

    def onClosingConstraints(self):
        """Close constraints page"""
        self.close()
