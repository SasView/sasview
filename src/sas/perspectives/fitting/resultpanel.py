"""
FitPanel class contains fields allowing to fit  models and  data

:note: For Fit to be performed the user should check at least one parameter
    on fit Panel window.

"""
import wx
import wx.lib.newevent
from wx.aui import AuiNotebook as Notebook

from sas.guiframe.panel_base import PanelBase
from sas.guiframe.events import StatusEvent

(PlotResultEvent, EVT_PLOT_RESULT) = wx.lib.newevent.NewEvent()


class ResultPanel(Notebook, PanelBase):
    """
    FitPanel class contains fields allowing to fit  models and  data

    :note: For Fit to be performed the user should check at least one parameter
        on fit Panel window.

    """
    ## Internal name for the AUI manager
    window_name = "Result panel"
    ## Title to appear on top of the window
    window_caption = "Result Panel"
    CENTER_PANE = True

    def __init__(self, parent, manager=None, *args, **kwargs):
        """
        """
        style = ((wx.aui.AUI_NB_WINDOWLIST_BUTTON
                 | wx.aui.AUI_NB_DEFAULT_STYLE
                 | wx.CLIP_CHILDREN)
                 & ~wx.aui.AUI_NB_CLOSE_ON_ACTIVE_TAB)
        Notebook.__init__(self, parent, -1, style=style)
        PanelBase.__init__(self, parent)
        self.frame = parent
        self.Bind(EVT_PLOT_RESULT, self.on_plot_results)
        self.frame.Bind(wx.EVT_CLOSE, self.on_close)
        self._manager = None

    def on_close(self, event):
        if event.CanVeto():
            self.frame.Hide()
            event.Veto()
        else:
            event.Skip()

    def on_plot_results(self, event):
        self.frame.Show()
        result = event.result[0][0]
        if hasattr(result, 'convergence'):
            from bumps.gui.convergence_view import ConvergenceView
            best, pop = result.convergence[:, 0], result.convergence[:, 1:]
            self.get_panel(ConvergenceView).update(best, pop)
        if hasattr(result, 'uncertainty_state'):
            from bumps.gui.uncertainty_view import UncertaintyView, CorrelationView, TraceView
            from bumps.dream.stats import var_stats, format_vars
            stats = var_stats(result.uncertainty_state.draw())
            msg = format_vars(stats)
            self.get_panel(CorrelationView).update(result.uncertainty_state)
            self.get_panel(UncertaintyView).update((result.uncertainty_state, stats))
            self.get_panel(TraceView).update(result.uncertainty_state)
            # TODO: stats should be stored in result rather than computed in bumps UncertaintyView
            wx.PostEvent(self.frame.parent,
                         StatusEvent(status=msg, info="info"))
            print

    def get_frame(self):
        return self.frame

    def add_panel(self, panel):
        self.AddPage(panel, panel.title)

    def get_panel(self, panel_class):
        for idx in range(self.PageCount):
            if self.GetPageText(idx) == panel_class.title:
                return self.GetPage(idx)
        else:
            panel = panel_class(self)
            self.add_panel(panel)
            return panel
