import os

from glue_jupyter.view import IPyWidgetView
from ..volume_viewer import VispyVolumeViewerMixin
from .viewer_state_widget import Volume3DViewerStateWidget
from .layer_state_widget import Volume3DLayerStateWidget
from ...common.jupyter.toolbar import VispyJupyterToolbar
from ...scatter.jupyter.layer_state_widget import Scatter3DLayerStateWidget
from ..layer_artist import VolumeLayerArtist
from ...scatter.layer_artist import ScatterLayerArtist

__all__ = ['JupyterVispyVolumeViewer']


class JupyterVispyVolumeViewer(VispyVolumeViewerMixin, IPyWidgetView):

    _options_cls = Volume3DViewerStateWidget
    _layer_style_widget_cls = Volume3DLayerStateWidget
    _layer_style_widget_cls = {VolumeLayerArtist: Volume3DLayerStateWidget,
                               ScatterLayerArtist: Scatter3DLayerStateWidget}
    _toolbar_cls = VispyJupyterToolbar

    def __init__(self, *args, **kwargs):
        # Vispy and jupyter_rfb don't work correctly on Linux unless DISPLAY is set
        if 'DISPLAY' not in os.environ:
            os.environ['DISPLAY'] = ':0'
        super().__init__(*args, **kwargs)
        self.setup_widget_and_callbacks()
        self.create_layout()

    @property
    def figure_widget(self):
        return self._vispy_widget.canvas._backend
