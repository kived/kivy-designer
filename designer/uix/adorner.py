from functools import partial
from kivy.properties import ObjectProperty, ListProperty, BoundedNumericProperty, AliasProperty, BooleanProperty, \
    OptionProperty
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.widget import Widget
from kivy.uix.sandbox import SandboxContent

class Adorner(RelativeLayout):
    '''Adorner adds frames, handles, buttons, and behavior to the current selected widget
    '''
    
    exclusive = False
    '''Denotes an exclusive :class:`~designer.adorner.Adorner` which will not
       be combined with any other :class:`~designer.adorner.Adorner`.
       :data:`exclusive` is a bool
    '''
    
    target = ObjectProperty()
    '''Reference to the target :class:`~kivy.uix.widget.Widget`
       :data:`target` is a :class:`~kivy.properties.ObjectProperty`
    '''
    
    border_width = BoundedNumericProperty(sp(2), min=0)
    '''Specifies the width of the frame border
       :data:`border_width` is a :class:`~kivy.properties.BoundedNumericProperty`
    '''
    
    button_width = BoundedNumericProperty(sp(36), min=0)
    '''Specifies the width and height of the buttons
       :data:`button_width` is a :class:`~kivy.properties.BoundedNumericProperty`
    '''
    
    handle_width = BoundedNumericProperty(sp(5), min=0)
    '''Specifies the width and height of the frame handles
       :data:`handle_width` is a :class:`~kivy.properties.BoundedNumericProperty`
    '''
    
    def get_button_size(self):
        return self.button_width, self.button_width
    def set_button_size(self, size):
        self.button_width = size[0]
    button_size = AliasProperty(get_button_size, set_button_size, bind=('button_width',))
    '''Alias property which specifies the size of the buttons
       :data:`button_size` is a :class:`~kivy.properties.AliasProperty`
    '''
    
    def get_handle_size(self):
        return self.handle_width, self.handle_width
    def set_handle_size(self, size):
        self.handle_width = size[0]
    handle_size = AliasProperty(get_handle_size, set_handle_size, bind=('handle_width',))
    '''Alias property which specifies the size of the frame handles
       :data:`handle_size` is a :class:`~kivy.properties.AliasProperty`
    '''
    
    border_color = ListProperty([0.2, 0.2, 0.2, 0.5])
    '''Specifies the color of the frame border
       :data:`border_color` is a :class:`~kivy.properties.ListProperty`
    '''
    
    handle_color = ListProperty([0.2, 0.2, 0.2, 0.8])
    '''Specifies the color of the frame handles
       :data:`handle_color` is a :class:`~kivy.properties.ListProperty`
    '''
    
    top_buttons = ListProperty([])
    '''List of buttons for the top side
       :data:`top_buttons` is a :class:`~kivy.properties.ListProperty`
    '''
    
    left_buttons = ListProperty([])
    '''List of buttons for the left side
       :data:`left_buttons` is a :class:`~kivy.properties.ListProperty`
    '''

    right_buttons = ListProperty([])
    '''List of buttons for the right side
       :data:`right_buttons` is a :class:`~kivy.properties.ListProperty`
    '''

    bottom_buttons = ListProperty([])
    '''List of buttons for the bottom side
       :data:`bottom_buttons` is a :class:`~kivy.properties.ListProperty`
    '''

    top_left_corner = ObjectProperty(None, allownone=True)
    '''Reference to the button for the top left corner
       :data:`top_left_corner` is a :class:`~kivy.properties.ObjectProperty`
    '''
    
    top_right_corner = ObjectProperty(None, allownone=True)
    '''Reference to the button for the top right corner
       :data:`top_right_corner` is a :class:`~kivy.properties.ObjectProperty`
    '''

    bottom_left_corner = ObjectProperty(None, allownone=True)
    '''Reference to the button for the bottom left corner
       :data:`bottom_left_corner` is a :class:`~kivy.properties.ObjectProperty`
    '''

    bottom_right_corner = ObjectProperty(None, allownone=True)
    '''Reference to the button for the bottom rightcorner
       :data:`bottom_right_corner` is a :class:`~kivy.properties.ObjectProperty`
    '''
    
    center_widgets = ListProperty([])
    '''List of widgets for the center area
       :data:`center_widgets` is a :class:`~kivy.properties.ListProperty`
    '''
    
    def __init__(self, target=None, playground=None, **kwargs):
        self._target = None
        self.playground = playground
        super(Adorner, self).__init__(size_hint=(None, None), **kwargs)
        self.select(target)
        self.update = Clock.create_trigger(self._update)
        Clock.schedule_interval(self.update, 0)

    def select(self, widget):
        '''Select a target widget to adorn
        '''
        self.target = widget
    
    def on_top_buttons(self, _, buttons):
        self._update_buttons(self.ids['top'], buttons)
    
    def on_left_buttons(self, _, buttons):
        self._update_buttons(self.ids['left'], buttons)

    def on_right_buttons(self, _, buttons):
        self._update_buttons(self.ids['right'], buttons)

    def on_bottom_buttons(self, _, buttons):
        self._update_buttons(self.ids['bottom'], buttons)

    def on_center_widgets(self, _, buttons):
        self._update_buttons(self.ids['center'], buttons)
    
    def on_top_left_corner(self, _, button):
        self._update_buttons(self.ids['top_left'], [button])

    def on_top_right_corner(self, _, button):
        self._update_buttons(self.ids['top_right'], [button])

    def on_bottom_left_corner(self, _, button):
        self._update_buttons(self.ids['bottom_left'], [button])

    def on_bottom_right_corner(self, _, button):
        self._update_buttons(self.ids['bottom_right'], [button])

    def _update_buttons(self, container, buttons):
        add_widget = container.add_widget
        remove_widget = container.remove_widget
        for w in container.children[:]:
            remove_widget(w)
        for b in buttons:
            add_widget(b)
    
    def on_target(self, _, target):
        if self._target:
            self._target.unbind(pos=self._update, size=self._update)
        self._target = self.target
        self._update()
        self._adorn()
        self.target.bind(pos=self._update, size=self._update)
    
    # def to_relative_parent(self, target, parent):
    # 	x, y, p = target.x, target.y, target
    # 	while p != parent:
    # 		if not (p and hasattr(p, 'to_parent')):
    # 			return None
    # 		x, y = p.to_parent(x, y)
    # 		p = p.parent
    # 	return x, y
    
    def _update(self, *_):
        if self.target:
            t = self.target
            scale = self.playground.scale
            pos = self.playground.to_local(*t.to_window(t.pos[0] * scale, t.pos[1] * scale))
            self.pos = pos
            self.size = t.width * scale, t.height * scale
            self._adorn()
            return
        self.size = 0, 0
    
    def _adorn(self):
        pass
    
    @classmethod
    def applies_to(cls, widget):
        '''Determines if this adorner should be applied to the given :class:`~kivy.uix.widget.Widget`
        '''
        return False

try:
    from kivy.uix.behaviors import HoverBehavior
except ImportError:
    from kivy.uix.behaviors import _is_desktop
    class HoverBehavior(object):
        '''Implements mouse hover behavior on supported platforms.
        '''

        hover = BooleanProperty(False)
        hover_unsupported_value = BooleanProperty(True)

        def __init__(self, **kwargs):
            super(HoverBehavior, self).__init__(**kwargs)
            if _is_desktop:
                from kivy.core.window import Window
                Window.bind(mouse_pos=self.on_mouse_pos)
            else:
                self.hover = self.hover_unsupported_value

        def on_mouse_pos(self, window, pos):
            pos = self.to_widget(*pos)
            if not self.hover and self.collide_point(*pos):
                self.hover = True
            elif self.hover and not self.collide_point(*pos):
                self.hover = False

class AdornerButton(HoverBehavior, Button):
    pass

class RootAdorner(Adorner):
    exclusive = True
    
    def __init__(self, **kwargs):
        kwargs['border_color'] = 0, 0, 0, 0
        super(RootAdorner, self).__init__(**kwargs)
    
    @classmethod
    def applies_to(cls, widget):
        return isinstance(widget.parent, SandboxContent)

class BoxLayoutAdorner(Adorner):
    def __init__(self, **kwargs):
        self.bleft = AdornerButton(text='<', size=self.button_size)
        self.bright = AdornerButton(text='>', size=self.button_size)
        self.bup = AdornerButton(text='^', size=self.button_size)
        self.bdown = AdornerButton(text='v', size=self.button_size)
        super(BoxLayoutAdorner, self).__init__(**kwargs)
        self.left_buttons.append(self.bleft)
        self.right_buttons.append(self.bright)
        self.top_buttons.append(self.bup)
        self.bottom_buttons.append(self.bdown)
        self.bleft.bind(on_press=partial(self.move, 1))
        self.bright.bind(on_press=partial(self.move, -1))
        self.bup.bind(on_press=partial(self.move, 1))
        self.bdown.bind(on_press=partial(self.move, -1))

    def move(self, dir, *_):
        parent = self.target.parent
        children = parent.children[:]
        for child in children:
            parent.remove_widget(child)
        idx = children.index(self.target)
        children[idx] = children[idx + dir]
        children[idx + dir] = self.target
        for child in reversed(children):
            parent.add_widget(child)

    def _adorn(self):
        layout = self.target.parent
        assert isinstance(layout, BoxLayout)
        
        layout_size = len(layout.children)
        if layout_size < 2:
            self.bleft.disabled = True
            self.bright.disabled = True
            self.bup.disabled = True
            self.bdown.disabled = True
            return
        
        layout_pos = layout.children.index(self.target)
        at_front = (layout_pos < (layout_size - 1))
        at_end = (layout_pos > 0)
        
        if layout.orientation == 'horizontal':
            self.bleft.disabled = not at_front
            self.bright.disabled = not at_end
            self.bup.disabled = True
            self.bdown.disabled = True
        else:
            self.bleft.disabled = True
            self.bright.disabled = True
            self.bup.disabled = not at_front
            self.bdown.disabled = not at_end
    
    @classmethod
    def applies_to(cls, widget):
        return isinstance(widget.parent, BoxLayout)

class Handle(Widget):
    color = ListProperty([0.2, 0.2, 0.2, 0.8])
    
    move_vertical = OptionProperty('none', options=('none', 'up', 'down'))
    move_horizontal = OptionProperty('none', options=('none', 'left', 'right'))

class ResizeAdorner(Adorner):
    def __init__(self, **kwargs):
        self.htop = Handle(move_vertical='up', size=self.handle_size, color=self.handle_color)
        self.hleft = Handle(move_horizontal='left', size=self.handle_size, color=self.handle_color)
        self.hright = Handle(move_horizontal='right', size=self.handle_size, color=self.handle_color)
        self.hbottom = Handle(move_vertical='down', size=self.handle_size, color=self.handle_color)
        self.htl = Handle(move_vertical='up', move_horizontal='left', size=self.handle_size, color=self.handle_color)
        self.htr = Handle(move_vertical='up', move_horizontal='right', size=self.handle_size, color=self.handle_color)
        self.hbl = Handle(move_vertical='down', move_horizontal='left', size=self.handle_size, color=self.handle_color)
        self.hbr = Handle(move_vertical='down', move_horizontal='right', size=self.handle_size, color=self.handle_color)
        self.moving = None
        self.resizing = None
        self.moving_pos = 0, 0
        self.dragpop_touch = None
        self.dragpop_pos = None
        super(ResizeAdorner, self).__init__(**kwargs)
        self.htop.bind(on_touch_down=self._start_dragging)
        self.hleft.bind(on_touch_down=self._start_dragging)
        self.hright.bind(on_touch_down=self._start_dragging)
        self.hbottom.bind(on_touch_down=self._start_dragging)
        self.htl.bind(on_touch_down=self._start_dragging)
        self.htr.bind(on_touch_down=self._start_dragging)
        self.hbl.bind(on_touch_down=self._start_dragging)
        self.hbr.bind(on_touch_down=self._start_dragging)
        
        center = self.ids['center']
        center.add_widget(self.htop)
        self.htop.pos_hint = {'center_x': 0.5, 'center_y': 1}
        center.add_widget(self.hleft)
        self.hleft.pos_hint = {'center_x': 0, 'center_y': 0.5}
        center.add_widget(self.hright)
        self.hright.pos_hint = {'center_x': 1, 'center_y': 0.5}
        center.add_widget(self.hbottom)
        self.hbottom.pos_hint = {'center_x': 0.5, 'center_y': 0}
        center.add_widget(self.htl)
        self.htl.pos_hint = {'center_x': 0, 'center_y': 1}
        center.add_widget(self.htr)
        self.htr.pos_hint = {'center_x': 1, 'center_y': 1}
        center.add_widget(self.hbl)
        self.hbl.pos_hint = {'center_x': 0, 'center_y': 0}
        center.add_widget(self.hbr)
        self.hbr.pos_hint = {'center_x': 1, 'center_y': 0}
        
        center.bind(on_touch_down=self._start_dragmove)
        
        self.count = 0
    
    def _start_dragmove(self, center, touch):
        if super(FloatLayout, center).on_touch_down(touch):
            return True
        
        if center.collide_point(*touch.pos):
            touch.grab(self)
            self.moving = center
            self.moving_pos = self.playground.to_local(*center.to_window(*touch.pos))
            self.dragpop_touch = touch
            self.dragpop_pos = self.moving_pos
            Clock.schedule_once(self._start_dragpop, 1)
            return True
    
    def _start_dragpop(self, *_):
        tolerance = self.playground.drag_tolerance
        deltapos = abs(self.dragpop_pos[0] - Window.mouse_pos[0]), abs(self.dragpop_pos[1] - Window.mouse_pos[1])
        if deltapos[0] > tolerance or deltapos[1] > tolerance:
            self.dragpop_touch.ungrab(self)
            self.playground.prepare_widget_dragging(self.dragpop_touch, delay=0)
            self.dragpop_touch = None
    
    def _start_dragging(self, handle, touch):
        if handle.collide_point(*touch.pos):
            touch.grab(self)
            self.resizing = handle
            self.moving_pos = self.playground.to_local(*handle.to_window(*touch.pos))
            return True
    
    def on_touch_move(self, touch):
        if touch.grab_current is self and self.moving_pos:
            pos = self.playground.to_local(*touch.pos)
            dx = pos[0] - self.moving_pos[0]
            dy = pos[1] - self.moving_pos[1]
            self.moving_pos = pos
            
            if self.resizing:
                vertical = self.resizing.move_vertical
                horizontal = self.resizing.move_horizontal
                
                if vertical != 'none':
                    dy *= -1 if vertical == 'down' else 1
                    old_height = self.target.height
                    new_height = self.target.height + dy
                    self.target.size_hint_y = None
                    self.target.height = new_height
                    if vertical == 'down':
                        self.target.y -= new_height - old_height
                
                if horizontal != 'none':
                    dx *= -1 if horizontal == 'left' else 1
                    new_width = self.target.width + dx
                    self.target.size_hint_x = None
                    self.target.width = new_width
                    if horizontal == 'left':
                        self.target.x -= dx
            elif self.moving:
                self.target.x += dx
                self.target.y += dy

            return True
    
    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            self.moving = None
            self.resizing = None
            self.moving_pos = 0, 0
            Clock.unschedule(self._start_dragpop)
            return True
    
    @classmethod
    def applies_to(cls, widget):
        return isinstance(widget.parent, FloatLayout)

class AdornerFactory(object):
    
    adorners = [
        RootAdorner,
        BoxLayoutAdorner,
        ResizeAdorner,
    ]
    
    def __init__(self):
        self._types = {(a,):a for a in self.adorners}
    
    def _get_adorner_type_for(self, bases):
        bases = tuple(bases)
        type_ = self._types.get(bases, None)
        if not type_:
            type_ = type('+'.join([b.__name__ for b in bases]), bases=bases)
        return type_
    
    def get_adorner_for(self, widget):
        bases = []
        for adorner in self.adorners:
            if adorner.applies_to(widget):
                if adorner.exclusive:
                    return adorner
                bases.append(adorner)
        if bases:
            return self._get_adorner_type_for(bases)

Factory = AdornerFactory()
get_adorner_for = Factory.get_adorner_for

__all__ = ['get_adorner_for']
