from functools import partial
from kivy.properties import ObjectProperty, ListProperty, BoundedNumericProperty, AliasProperty, BooleanProperty, \
    OptionProperty
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.event import EventDispatcher
from kivy.metrics import sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.sandbox import SandboxContent

from designer.uix.inversecolor import InverseColor
from designer import helper_functions as helpers
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.widget import Widget


class AdornerBase(RelativeLayout):
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
    
    border_color = ListProperty([0.5, 0.5, 0.9, 0.5])
    '''Specifies the color of the frame border
       :data:`border_color` is a :class:`~kivy.properties.ListProperty`
    '''
    
    handle_color = ListProperty([0.3, 0.3, 1., 0.8])
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
    
    do_reparent = BooleanProperty(True)
    '''Indicate whether this adorner should reparent the widget
       :data:`do_reparent` is a :class:`~kivy.properties.BooleanProperty`
    '''
    
    do_translate = BooleanProperty(False)
    '''Indicate whether this adorner should translate the widget
       :data:`do_translate` is a :class:`~kivy.properties.BooleanProperty`
    '''
    
    def __init__(self, target=None, playground=None, **kwargs):
        self._target = None
        self.playground = playground
        super(AdornerBase, self).__init__(size_hint=(None, None), **kwargs)
        self.select(target)
        self.update = Clock.create_trigger(self._update)
        Clock.schedule_interval(self.update, 0)
        
        self.ids['center'].bind(on_touch_down=self.on_center_touch_down,
                                on_touch_move=self.on_center_touch_move,
                                on_touch_up=self.on_center_touch_up)

    def select(self, widget):
        '''Select a target widget to adorn
        '''
        self.target = widget
        self._update()
    
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
        else:
            self.size = 0, 0
    
    def _adorn(self):
        pass
    
    @classmethod
    def applies_to(cls, widget):
        '''Determines if this adorner should be applied to the given :class:`~kivy.uix.widget.Widget`
        '''
        return False
    
    def on_center_touch_down(self, center, touch, dispatch_children=True):
        if 'adorner_passoff' in touch.ud and touch.ud['adorner_passoff']:
            del touch.ud['adorner_passoff']
            dispatch_children = False
        
        if dispatch_children and super(FloatLayout, center).on_touch_down(touch):
            return True
        
        if (self.do_reparent or self.do_translate) and center.collide_point(*touch.pos):
            touch.grab(center)
            self.moving = center
            self.moving_pos = self.playground.to_widget(*center.to_window(*touch.pos))
            return True
    
    def on_center_touch_move(self, center, touch):
        if touch.grab_current is center and self.moving_pos:
            pos = self.playground.to_widget(*center.to_window(*touch.pos))
            dx, dy = pos[0] - self.moving_pos[0], pos[1] - self.moving_pos[1]
            self.moving_pos = pos
            
            if self.moving:
                if self.do_reparent and (not self.target.parent.collide_point(*pos) or (
                        not self.do_translate and not self.target.collide_point(*pos))):
                    self.on_center_touch_up(center, touch)
                    self.playground.prepare_widget_dragging(touch, delay=0)
                elif self.do_translate:
                    helpers.move_widget(self.target, x=self.target.x + dx, y=self.target.y + dy)
                    self.count = getattr(self, 'count', 0) + 1

            return True
    
    def on_center_touch_up(self, center, touch):
        if touch.grab_current is center:
            touch.ungrab(center)
            self.moving = None
            self.moving_pos = 0, 0
            return True
    

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

class AdornerToggleButton(HoverBehavior, ToggleButton):
    pass

class RootAdorner(AdornerBase):
    exclusive = True
    
    def __init__(self, **kwargs):
        kwargs['border_color'] = 0, 0, 0, 0
        kwargs['do_reparent'] = False
        super(RootAdorner, self).__init__(**kwargs)
    
    @classmethod
    def applies_to(cls, widget):
        return isinstance(widget.parent, SandboxContent)

class PlaygroundDragAdorner(AdornerBase):
    exclusive = True

    def __init__(self, **kwargs):
        kwargs['do_reparent'] = False
        kwargs['do_translate'] = False
        super(PlaygroundDragAdorner, self).__init__(**kwargs)
        self.ids['border_frame'].opacity = 0
    
    @classmethod
    def applies_to(cls, widget):
        from designer.playground import PlaygroundDragElement
        return isinstance(widget.parent, PlaygroundDragElement)

class BlockAdorner(AdornerBase):
    def __init__(self, **kwargs):
        self.bleft = AdornerButton(text='<', size=self.button_size)
        self.bright = AdornerButton(text='>', size=self.button_size)
        self.bup = AdornerButton(text='^', size=self.button_size)
        self.bdown = AdornerButton(text='v', size=self.button_size)
        super(BlockAdorner, self).__init__(**kwargs)
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
        
        self.bleft.disabled = True
        self.bright.disabled = True
        self.bup.disabled = True
        self.bdown.disabled = True
        
        if isinstance(layout, BoxLayout):
            lvals = helpers.BoxLayout.widget_position(self.target, layout)
            
            if layout.orientation == 'horizontal':
                self.bleft.disabled = lvals['at_front']
                self.bright.disabled = lvals['at_end']
            else:
                self.bup.disabled = lvals['at_front']
                self.bdown.disabled = lvals['at_end']
        
        super(BlockAdorner, self)._adorn()
    
    @classmethod
    def applies_to(cls, widget):
        return isinstance(widget.parent, BoxLayout)

class Handle(InverseColor):
    color = ListProperty([0.6, 0.5, 0.9, 0.8])
    
    move_vertical = OptionProperty('none', options=('none', 'up', 'down'))
    move_horizontal = OptionProperty('none', options=('none', 'left', 'right'))

class ResizeAdorner(AdornerBase):
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
        super(ResizeAdorner, self).__init__(**kwargs)
        self.htop.bind(on_touch_down=self._start_dragging)
        self.hleft.bind(on_touch_down=self._start_dragging)
        self.hright.bind(on_touch_down=self._start_dragging)
        self.hbottom.bind(on_touch_down=self._start_dragging)
        self.htl.bind(on_touch_down=self._start_dragging)
        self.htr.bind(on_touch_down=self._start_dragging)
        self.hbl.bind(on_touch_down=self._start_dragging)
        self.hbr.bind(on_touch_down=self._start_dragging)
        
        self.htop.pos_hint = {'center_x': 0.5, 'center_y': 1}
        self.hleft.pos_hint = {'center_x': 0, 'center_y': 0.5}
        self.hright.pos_hint = {'center_x': 1, 'center_y': 0.5}
        self.hbottom.pos_hint = {'center_x': 0.5, 'center_y': 0}
        self.htl.pos_hint = {'center_x': 0, 'center_y': 1}
        self.htr.pos_hint = {'center_x': 1, 'center_y': 1}
        self.hbl.pos_hint = {'center_x': 0, 'center_y': 0}
        self.hbr.pos_hint = {'center_x': 1, 'center_y': 0}
        
        self.count = 0
    
    def _start_dragging(self, handle, touch):
        if handle.disabled:
            return False
        
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
                    down = vertical == 'down'
                    dy = pos[1]
                    base_pos = self.target.top if down else self.target.y
                    orig_height = self.target.height
                    new_height = max(0, (base_pos - dy) if down else (dy - base_pos))
                    helpers.resize_widget(self.target, height=new_height)
                    real_height = self.target.height
                    if down and self.do_translate:
                        helpers.move_widget(self.target, y=self.target.y + orig_height - real_height)
                
                if horizontal != 'none':
                    left = horizontal == 'left'
                    dx = pos[0]
                    base_pos = self.target.right if left else self.target.x
                    orig_width = self.target.width
                    new_width = max(0, (base_pos - dx) if left else (dx - base_pos))
                    helpers.resize_widget(self.target, width=new_width)
                    real_width = self.target.width
                    if left and self.do_translate:
                        helpers.move_widget(self.target, x=self.target.x + orig_width - real_width)

            return True
    
    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            self.resizing = None
            self.moving_pos = 0, 0
            return True
    
    def _adorn(self):
        layout = self.target.parent
        center = self.ids['center']
        
        def enable(handles, enabled):
            def do_enable(h):
                if h not in center.children:
                    if h.parent:
                        h.parent.remove_widget(h)
                    center.add_widget(h)
            def do_disable(h):
                if h in center.children:
                    center.remove_widget(h)
            
            do = do_enable if enabled else do_disable
            for handle in handles:
                do(handle)
                #handle.disabled = not enabled
                #handle.opacity = 1 if enabled else 0
                #handle.color = handle.color[:3] + [0.8 if enabled else 0]

        if isinstance(layout, BoxLayout):
            self.do_translate = False
            enable((self.hbl, self.hbr, self.htl, self.htr, self.htop, self.hbottom, self.hleft, self.hright), False)
            lvals = helpers.BoxLayout.widget_position(self.target, layout)
            if layout.orientation == 'horizontal':
                enable((self.htop,), self.target.valign != 'top')
                enable((self.hbottom,), self.target.valign != 'bottom')
                enable((self.hleft,), not lvals['at_front'])
                enable((self.hright,), not lvals['at_end'])
            else:
                enable((self.hleft,), self.target.halign != 'left')
                enable((self.hright,), self.target.halign != 'right')
                enable((self.htop,), not lvals['at_front'])
                enable((self.hbottom,), not lvals['at_end'])
        else:
            enable((self.hbl, self.hbr, self.htl, self.htr, self.htop, self.hbottom, self.hleft, self.hright), True)
            self.do_translate = True
        
        super(ResizeAdorner, self)._adorn()
    
    @classmethod
    def applies_to(cls, widget):
        return isinstance(widget.parent, (FloatLayout, BoxLayout))

class AnchorAdorner(AdornerBase):
    def __init__(self, **kwargs):
        self.aenable = AdornerToggleButton(text='A', size=self.button_size)
        self.atl = ToggleButton(text='tl', group='anchor', size_hint=(None, None), size=self.button_size, pos_hint={'x': 0, 'top': 1})
        self.atop = ToggleButton(text='top', group='anchor', size_hint=(None, None), size=self.button_size, pos_hint={'center_x': 0.5, 'top': 1})
        self.atr = ToggleButton(text='tr', group='anchor', size_hint=(None, None), size=self.button_size, pos_hint={'right': 1, 'top': 1})
        self.aleft = ToggleButton(text='left', group='anchor', size_hint=(None, None), size=self.button_size, pos_hint={'x': 0, 'center_y': 0.5})
        self.acenter = ToggleButton(text='center', group='anchor', size_hint=(None, None), size=self.button_size, pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.aright = ToggleButton(text='right', group='anchor', size_hint=(None, None), size=self.button_size, pos_hint={'right': 1, 'center_y': 0.5})
        self.abl = ToggleButton(text='bl', group='anchor', size_hint=(None, None), size=self.button_size, pos_hint={'x': 0, 'y': 0})
        self.abottom = ToggleButton(text='bottom', group='anchor', size_hint=(None, None), size=self.button_size, pos_hint={'center_x': 0.5, 'y': 0})
        self.abr = ToggleButton(text='br', group='anchor', size_hint=(None, None), size=self.button_size, pos_hint={'right': 1, 'y': 0})
        self.afree = ToggleButton(text='free', group='anchor', size_hint=(None, None), size=self.button_size, pos_hint={'y': 1, 'x': 0.7})
        super(AnchorAdorner, self).__init__(**kwargs)
        self.top_right_corner = self.aenable
        
        self.atl.bind(on_release=lambda *_: helpers.anchor_widget(self.target, 'x', 'top'))
        self.atop.bind(on_release=lambda *_: helpers.anchor_widget(self.target, 'center_x', 'top'))
        self.atr.bind(on_release=lambda *_: helpers.anchor_widget(self.target, 'right', 'top'))
        self.aleft.bind(on_release=lambda *_: helpers.anchor_widget(self.target, 'x', 'center_y'))
        self.acenter.bind(on_release=lambda *_: helpers.anchor_widget(self.target, 'center_x', 'center_y'))
        self.aright.bind(on_release=lambda *_: helpers.anchor_widget(self.target, 'right', 'center_y'))
        self.abl.bind(on_release=lambda *_: helpers.anchor_widget(self.target, 'x', 'y'))
        self.abottom.bind(on_release=lambda *_: helpers.anchor_widget(self.target, 'center_x', 'y'))
        self.abr.bind(on_release=lambda *_: helpers.anchor_widget(self.target, 'right', 'y'))

    def _adorn(self):
        layout = self.target.parent
        center = self.ids['center']

        def enable(handles, enabled):
            def do_enable(h):
                if h not in center.children:
                    if h.parent:
                        h.parent.remove_widget(h)
                    center.add_widget(h)

            def do_disable(h):
                if h in center.children:
                    center.remove_widget(h)

            do = do_enable if enabled else do_disable
            for handle in handles:
                do(handle)
        
        enable((self.atl, self.atop, self.atr, self.aleft, self.acenter, self.aright, self.abl, self.abottom, self.abr, self.afree),
               self.aenable.state == 'down')

        super(AnchorAdorner, self)._adorn()
    
    @classmethod
    def applies_to(cls, widget):
        return isinstance(widget.parent, (FloatLayout,))

class Adorner(EventDispatcher):
    
    adornment_layer = ObjectProperty()
    playground = ObjectProperty()
    
    target = ObjectProperty(None, allownone=True)
    active_adorners = ListProperty([])
    
    _current_adorner = ObjectProperty(None, allownone=True)
    
    def get_current_adorner(self):
        return self._current_adorner
    def set_current_adorner(self, adorner):
        if self._current_adorner and self._current_adorner.parent:
            self._current_adorner.parent.remove_widget(self._current_adorner)
            self._current_adorner = None
        self._current_adorner = adorner
        self.adornment_layer.add_widget(adorner)
        adorner.select(self.target)
    current_adorner = AliasProperty(get_current_adorner, set_current_adorner, bind=('_current_adorner',))
    
    adorners = [
        RootAdorner,
        PlaygroundDragAdorner,
        BlockAdorner,
        ResizeAdorner,
        AnchorAdorner,
    ]
    
    def __init__(self, **kwargs):
        super(Adorner, self).__init__(**kwargs)
        self.adorners = [a(playground=self.playground) for a in self.adorners[:]]
        self.null_adorner = AdornerBase(playground=self.playground)
    
    def select(self, widget):
        self.target = widget
    
    def on_target(self, *_):
        self.target.bind(parent=self.update_adorners)
        self.update_adorners()
    
    def update_adorners(self, *_):
        adorners = self._get_adorners_for(self.target)
        if adorners != self.active_adorners:
            self.active_adorners = adorners
            self.current_adorner = self.active_adorners[0]
        else:
            self.current_adorner.select(self.target)
    
    def _get_adorners_for(self, widget):
        adorners = []
        for adorner in self.adorners:
            if adorner.applies_to(widget):
                if adorner.exclusive:
                    return [adorner]
                adorners.append(adorner)
        return adorners or [self.null_adorner]
    
    def on_touch_down(self, touch):
        return self.current_adorner.on_touch_down(touch)
    

__all__ = ['Adorner']
