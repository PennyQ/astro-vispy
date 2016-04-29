from __future__ import absolute_import, division, print_function

import sys

import numpy as np
from vispy import scene, app
from vispy.geometry import create_cube

from glue.external.echo import CallbackProperty, add_callback
from glue.external.qt import QtGui, get_qapp
from glue.utils import nonpartial

class VispyWidget(QtGui.QWidget):

    visible_axes = CallbackProperty()
    rotate_view = CallbackProperty()

    def __init__(self, parent=None):

        super(VispyWidget, self).__init__(parent=parent)

        # Prepare Vispy canvas. We set the depth_size to 24 to avoid issues
        # with isosurfaces on MacOS X
        self.canvas = scene.SceneCanvas(keys='interactive', show=False,
                                        config={'depth_size': 24})

        # Set up a viewbox
        self.view = self.canvas.central_widget.add_view()
        self.view.parent = self.canvas.scene

        # Set whether we are emulating a 3D texture. This needs to be enabled
        # as a workaround on Windows otherwise VisPy crashes.
        self.emulate_texture = (sys.platform == 'win32' and
                                sys.version_info[0] < 3)

        self.axis_transform = scene.STTransform()
        self.limit_transforms = {}

        # Add a 3D cube to show us the unit cube. The 1.001 factor is to make 
        # sure that the grid lines are not 'hidden' by volume renderings on the 
        # front side due to numerical precision.
        vertices, filled_indices, outline_indices = create_cube()
        self.axis = scene.visuals.Mesh(vertices['position'],
                                       outline_indices,
                                       color=(1,1,1), mode='lines')
        self.axis.transform = self.axis_transform
        self.view.add(self.axis)

        # Create a turntable camera. For now, this is the only camerate type
        # we support, but if we support more in future, we should implement
        # that here

        # Remove the fov=60 here to solve the mismatch of selection problem
        self.view.camera = scene.cameras.TurntableCamera(parent=self.view.scene, fov=60, distance=2.0)

        # Add the native canvas widget to this widget
        layout = QtGui.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas.native)
        self.setLayout(layout)

        # We need to call render here otherwise we'll later encounter an OpenGL
        # program validation error.
        self.canvas.render()

        # Add a timer to control the view rotate
        self.timer = app.Timer(connect=self.rotate)
        self.stretch_value = None # add a temperary variable to store stretch here, remove later
        self.rotate_slider_val = 0.0
        self.rotate_speed = 0.0
        
        # Set up callbacks
        add_callback(self, 'visible_axes', nonpartial(self._toggle_axes))
        add_callback(self, 'rotate_view', nonpartial(self._toggle_rotate))

    def _toggle_axes(self):
        if self.visible_axes:
            self.axis.parent = self.view.scene
        else:
            self.axis.parent = None
        self.canvas.update()

    def _toggle_rotate(self):
        if self.rotate_view:
            self.timer.start(0.1)
        else:
            self.timer.stop()

    def add_data_visual(self, visual):
        self.limit_transforms[visual] = scene.STTransform()
        visual.transform = self.limit_transforms[visual]
        self.view.add(visual)

    def _update_stretch(self, *stretch):
        self.axis_transform.scale = stretch
        self._update_limits()

    def _update_rotate(self, rotate):
        self.rotate_slider_val = rotate

    # For update transform for visuals
    def _update_limits(self):

        if len(self.limit_transforms) == 0:
            return

        if (self.options.x_min is None or self.options.x_max is None or
            self.options.y_min is None or self.options.y_max is None or
            self.options.z_min is None or self.options.z_max is None):
            raise Exception("We should never get here because if any data is "
                            "present, the limits should be set")

        scale = [2 / (self.options.x_max - self.options.x_min) * self.options.x_stretch,
                 2 / (self.options.y_max - self.options.y_min) * self.options.y_stretch,
                 2 / (self.options.z_max - self.options.z_min) * self.options.z_stretch]

        translate = [-0.5 * (self.options.x_min + self.options.x_max) * scale[0],
                     -0.5 * (self.options.y_min + self.options.y_max) * scale[1],
                     -0.5 * (self.options.z_min + self.options.z_max) * scale[2]]

        for visual in self.limit_transforms:
            self.limit_transforms[visual].scale = scale
            self.limit_transforms[visual].translate = translate

    def _reset_view(self):
        self.view.camera.reset()

    def rotate(self, event):
        self.view.camera.azimuth += self.rotate_slider_val

if __name__ == "__main__":

    from viewer_options import VispyOptionsWidget

    app = get_qapp()
    w = VispyWidget()
    d = VispyOptionsWidget(vispy_widget=w)
    d.show()

    positions = np.random.random((1000, 3))
    scat_visual = scene.visuals.Markers()
    scat_visual.set_data(positions, symbol='disc', edge_color=None, face_color='red')
    w.add_data_visual(scat_visual)

    d.x_min = 0
    d.x_max = +1

    d.y_min = 0
    d.y_max = +1

    d.z_min = 0
    d.z_max = +1

    w.show()
    app.exec_()
    app.quit()
