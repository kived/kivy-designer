from kivy.uix.widget import Widget
from kivy.graphics import Callback
from kivy.graphics.opengl import glBlendFunc, GL_ONE_MINUS_DST_COLOR, GL_ZERO, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA


class InverseColor(Widget):
    
    def __init__(self, **kwargs):
        super(InverseColor, self).__init__(**kwargs)
        
        with self.canvas.before:
            Callback(self._enable)
        with self.canvas.after:
            Callback(self._disable)
    
    def _enable(self, *_):
        if self.opacity == 1:
            glBlendFunc(GL_ONE_MINUS_DST_COLOR, GL_ZERO)
    
    def _disable(self, *_):
        if self.opacity == 1:
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
