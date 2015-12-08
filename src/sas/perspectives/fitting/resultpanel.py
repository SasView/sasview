"""
FitPanel class contains fields allowing to fit  models and  data

:note: For Fit to be performed the user should check at least one parameter
    on fit Panel window.

"""
import wx
import wx.lib.newevent
from wx.aui import AuiNotebook as Notebook

from bumps.gui.convergence_view import ConvergenceView
from bumps.gui.uncertainty_view import UncertaintyView, CorrelationView, TraceView
from bumps.dream.stats import var_stats, format_vars

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
        Notebook.__init__(self, parent, wx.ID_ANY, style=style)
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
            best, pop = result.convergence[:, 0], result.convergence[:, 1:]
            self._get_view(ConvergenceView).update(best, pop)
        else:
            self._del_view(ConvergenceView)
        if hasattr(result, 'uncertainty_state'):
            stats = var_stats(result.uncertainty_state.draw())
            msg = format_vars(stats)
            self._get_view(CorrelationView).update(result.uncertainty_state)
            self._get_view(UncertaintyView).update((result.uncertainty_state, stats))
            self._get_view(TraceView).update(result.uncertainty_state)
            # TODO: stats should be stored in result rather than computed in bumps UncertaintyView
            wx.PostEvent(self.frame.parent,
                         StatusEvent(status=msg, info="info"))
        else:
            for view in (CorrelationView, UncertaintyView, TraceView):
                self._del_view(view)

    def get_frame(self):
        return self.frame

    def _get_view(self, view_class):
        for idx in range(self.PageCount):
            if self.GetPageText(idx) == view_class.title:
                return self.GetPage(idx)
        else:
            panel = view_class(self)
            self.AddPage(panel, panel.title)
            return panel

    def _del_view(self, view_class):
        for idx in range(self.PageCount):
            if self.GetPageText(idx) == view_class.title:
                self.DeletePage(idx)

