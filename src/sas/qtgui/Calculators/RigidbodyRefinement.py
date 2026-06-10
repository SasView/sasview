import os

import pyausaxs as ausaxs

import sas.qtgui.Calculators.RigidbodyRefinementUI as RigidBodyRefinementUI
import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Plotting.PlotterData import Data1D


class RigidBodyRefinement:
    class BlockLoad:
        def __init__(self, pdbfile=None, datafile=None, splits=None):
            self.pdbfile = pdbfile
            self.datafile = datafile
            self.splits = splits
            self.line_size = 5

        def __str__(self):
            block = "load {\n"
            if self.pdbfile:  block += f"    pdb {self.pdbfile}\n"
            if self.datafile: block += f"    saxs {self.datafile}\n"
            if self.splits:   block += f"    split {', '.join(self.splits)}\n"
            block += "}\n\n"
            self.line_size = len(block.splitlines())
            return block

        def update(self, code: str) -> str:
            """Update the given code by replacing the current load block with the new one."""
            lines = code.splitlines()
            if self.line_size > 0:              # Remove the old block
                lines = lines[self.line_size:]
            return str(self) + "\n".join(lines) # Prepend the new block

    def __init__(self, *args):
        self.gui = RigidBodyRefinementUI.RigidBodyRefinementUI(*args)
        self.gui.set_load_pdb_hook(self.on_load_pdb)
        self.gui.set_load_data_hook(self.on_load_data)
        self.gui.finished.connect(self.on_finish)
        self.gui.validate_requested.connect(self.on_validate)
        self.gui.setValidElements(ausaxs.Rigidbody.get_valid_elements_and_arguments())

        self.block_load = self.BlockLoad()
        self.gui.setText(self.default_text())

    def on_finish(self, text: str):
        """Run the refinement script and display results."""
        self.gui.clearOutput()
        self.gui.setRunning(True)
        try:
            rigidbody = ausaxs.prepare_rigidbody_refinement(text)
            ausaxs.set_output_callback(self.gui.appendOutput)
            try:
                result = rigidbody.run()
            finally:
                ausaxs.reset_output_callback()
            self._send_results_to_data_explorer(result)
            self.gui.appendOutput("Refinement completed.")
        except Exception as e:
            self.gui.appendOutput(f"{e}")
        finally:
            self.gui.setRunning(False)

    def _send_results_to_data_explorer(self, res):
        """Send the refinement results (q, I, I_err, I_model) to the Data Explorer."""
        q, I, I_err, I_model = res[:, 0], res[:, 1], res[:, 2], res[:, 3]

        data_exp = Data1D(x=q, y=I, dy=I_err)
        data_exp.title = "Rigidbody refinement (data)"
        data_exp.id = data_exp.title
        data_exp.xaxis(r'\rm{Q}', r'\AA^{-1}')
        data_exp.yaxis(r'\rm{Intensity}', 'cm^{-1}')

        data_model = Data1D(x=q, y=I_model)
        data_model.title = "Rigidbody refinement (model)"
        data_model.id = data_model.title
        data_model.xaxis(r'\rm{Q}', r'\AA^{-1}')
        data_model.yaxis(r'\rm{Intensity}', 'cm^{-1}')

        item_exp = GuiUtils.createModelItemWithPlot(data_exp, name=data_exp.title)
        GuiUtils.updateModelItemWithPlot(item_exp, data_model, name=data_model.title)
        GuiUtils.communicator.updateModelFromPerspectiveSignal.emit(item_exp)
        GuiUtils.communicator.forcePlotDisplaySignal.emit([item_exp, data_model])

    def on_validate(self, text: str):
        """Validate the script and display results in the output pane."""
        self.gui.clearOutput()
        try:
            rigidbody = ausaxs.prepare_rigidbody_refinement(text)
            rigidbody.validate()
            self.gui.appendOutput("Validation successful.")
        except Exception as e:
            self.gui.appendOutput(f"{e}")

    def on_load_pdb(self, path: str):
        pdbfile = os.path.basename(path)
        self.block_load.pdbfile = pdbfile
        self.gui.setText(self.block_load.update(self.gui.getText()))

    def on_load_data(self, path: str):
        datafile = os.path.basename(path)
        self.block_load.datafile = datafile
        self.gui.setText(self.block_load.update(self.gui.getText()))

    def on_set_splits(self, splits: list[str]):
        self.block_load.splits = splits
        self.gui.setText(self.block_load.update(self.gui.getText()))

    def show(self):
        self.gui.show()

    def default_text(self) -> str:
        return r"""output output/rigidbody/normal/
load {
    pdb test/sascalculator/data/LAR1-2.pdb
    saxs test/sascalculator/data/LAR1-2.dat
    split 9, 99
}
save initial_state.pdb
save trajectory.xyz
parameter_generator {
    iterations 3
    translate 1
    rotate 1
}

print "Initial chi2: {chi2_no_penalty}"
loop
    optimize_once
        on_improvement
            print {
                msg "{iteration}/{iterations_total}: Accepted with new chi2 {chi2_no_penalty}"
                colour green
            }
            save trajectory.xyz
        end
    end
end
save final_state.pdb
"""
