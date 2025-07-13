#Global
import ast
import logging
import traceback
import importlib.util
import re

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton

from sas.qtgui.Utilities.ModelEditors.TabbedEditor.ModelEditor import ModelEditor
from sas.qtgui.Calculators.Shape2SAS.UI.ConstraintsUI import Ui_Constraints
from sas.qtgui.Calculators.Shape2SAS.Tables.variableTable import VariableTable
from sas.qtgui.Calculators.Shape2SAS.ButtonOptions import ButtonOptions
from sas.sascalc.shape2sas.UserText import UserText

logger = logging.getLogger(__name__)

VAL_TYPE = str | int | float


class Constraints(QWidget, Ui_Constraints):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        #Setup GUI for Constraints
        self.constraintTextEditor = ModelEditor() #SasView's standard text editor
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

    def setConstraints(self, fit_params: str):
        """Insert the text into the constraints editor"""

        constraints = self.getConstraintText(fit_params)
        self.constraintTextEditor.txtEditor.setPlainText(constraints)
        self.createPlugin.setEnabled(True)

    @staticmethod
    def parseConstraintsText(
        text: str, fitPar: list[str], modelPars: list[str], modelVals: list[list[float]], checkedPars: list[str]
    ) -> tuple[list[str], str, str, list[list[bool]]]:
        """Parse the text in the constraints editor and return a dictionary of parameters"""

        print("Parsing constraints text.")
        print("Received input:")
        print(f"fitPar: {fitPar}")
        print(f"modelPars: {modelPars}")
        print(f"modelVals: {modelVals}")
        print(f"checkedPars: {checkedPars}")

        def as_ast(text: str):
            try:
                return ast.parse(text)
            except SyntaxError as e:
                # log most recent traceback error
                all_lines = traceback.format_exc().split('\n')
                last_lines = all_lines[-1:]
                traceback_to_show = '\n'.join(last_lines)
                logger.error(traceback_to_show)
                return None
        
        def parse_ast(tree: ast.AST):
            params = None
            imports = []
            constraints = []

            for node in ast.walk(tree):
                match node:
                    case ast.ImportFrom() | ast.Import():
                        imports.append(node)

                    case ast.Assign():
                        if node.targets[0].id == 'parameters':
                            params = node
                        else:
                            constraints.append(node)

            # params must be defined
            if params is None:
                logger.error("No parameters found in constraints text.")
                return None, None, None

            # ensure imports are valid
            #! not implemented yet

            return params, imports, constraints
        
        def extract_symbols(constraints: list[ast.AST]) -> tuple[list[str], list[str]]:
            """Extract all symbols used in the constraints."""
            lhs, rhs = set(), set()
            for node in constraints:
                # left-hand side of assignment
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        lhs.add(target.id)

                # right-hand side of assignment
                for value in ast.walk(node.value):
                    if isinstance(value, ast.Name):
                        rhs.add(value.id)

            return lhs, rhs

        def validate_symbols(lhs: list[str], rhs: list[str], fitPars: list[str]):
            """Check if all symbols in lhs and rhs are valid parameters."""
            # lhs is not allowed to contain fit parameters
            for symbol in lhs:
                if symbol in fitPars or symbol[1:] in fitPars:
                    logger.error(f"Symbol '{symbol}' is a fit parameter and cannot be used in constraints.")
                    raise ValueError(f"Symbol '{symbol}' is a fit parameter and cannot be assigned to.")
        
        def validate_imports(imports: list[ast.ImportFrom | ast.Import]):
            """Check if all imports are valid."""
            for imp in imports:
                if isinstance(imp, ast.ImportFrom):
                    if not importlib.util.find_spec(imp.module):
                        logger.error(f"Module '{imp.module}' not found.")
                        raise ModuleNotFoundError(f"No module named {imp.module}")
                elif isinstance(imp, ast.Import):
                    for name in imp.names:
                        if not importlib.util.find_spec(name.name):
                            logger.error(f"Module '{name.name}' not found.")
                            raise ModuleNotFoundError(f"No module named {name.name}")

        tree = as_ast(text)
        params, imports, constraints = parse_ast(tree)
        lhs, rhs = extract_symbols(constraints)
        validate_symbols(lhs, rhs, fitPar)
        validate_imports(imports)

        params = ast.unparse(params)
        imports = [ast.unparse(imp) for imp in imports]
        constraints = [ast.unparse(constraint) for constraint in constraints]
        symbols = (lhs, rhs)

        print("Finished parsing constraints text.")
        print(f"Parsed parameters: {params}")
        print(f"Parsed imports: {imports}")
        print(f"Parsed constraints: {constraints}")
        print(f"Symbols used: {symbols}")

        return UserText(imports, params, constraints, symbols), checkedPars

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
