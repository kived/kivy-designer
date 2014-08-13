from functools import partial

from kivy.properties import ObjectProperty, ListProperty, BoundedNumericProperty, AliasProperty, BooleanProperty, \
    OptionProperty, StringProperty, NumericProperty
from designer.operations import ManipulatorTranslateOperation, ManipulatorResizeOperation, ManipulatorIndexOperation, \
    ManipulatorNullOperation
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Line, Ellipse
from kivy.metrics import sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.sandbox import SandboxContent
from designer.uix.inversecolor import InverseColor
from designer import helper_functions as helpers
from kivy.uix.togglebutton import ToggleButton


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


class AdornerImageButton(AdornerButton):
    source = StringProperty('')


class Handle(InverseColor):
    color = ListProperty([0.6, 0.5, 0.9, 0.8])

    move_vertical = OptionProperty('none', options=('none', 'up', 'down'))
    move_horizontal = OptionProperty('none', options=('none', 'left', 'right'))


class AdornerBase(RelativeLayout):
    '''Adorner adds frames, handles, buttons, and behavior to the current selected widget
    '''
    
    exclusive = False
    '''Denotes an exclusive :class:`~designer.adorner.Adorner` which will not
       be combined with any other :class:`~designer.adorner.Adorner`.
       :data:`exclusive` is a bool
    '''
    
    target = ObjectProperty(allownone=True)
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
    
    border_normal_color = ListProperty([0.5, 0.5, 0.9, 0.5])
    '''Specifies the normal color of the frame border
       :data:`border_normal_color` is a :class:`~kivy.properties.ListProperty`
    '''
    
    border_highlight_color = ListProperty([0.5, 0.9, 0.5, 0.5])
    '''Specifies the highlight color of the frame border
       :data:`border_highlight_color` is a :class:`~kivy.properties.ListProperty`
    '''
    
    def get_border_color(self):
        return self.border_highlight_color if self.highlight else self.border_normal_color
    def set_border_color(self, value):
        self.border_normal_color = self.border_highlight_color = value
    border_color = AliasProperty(get_border_color, set_border_color,
                                 bind=('border_normal_color', 'border_highlight_color', 'highlight'))

    handle_color = ListProperty([0.3, 0.3, 1., 0.8])
    '''Specifies the color of the frame handles
       :data:`handle_color` is a :class:`~kivy.properties.ListProperty`
    '''

    button_area = ObjectProperty()
    center_area = ObjectProperty()
    
    highlight = BooleanProperty(False)
    '''Indicate whether the widget should be outlined with the highlight color
       :data:`highlight` is a :class:`~kivy.properties.BooleanProperty`
    '''
    
    icon = StringProperty('')
    '''Specifies the path to the icon to use for the adorner
       :data:`icon` is a :class:`~kivy.properties.StringProperty`
    '''

    def __init__(self, target=None, playground=None, manipulator=None, **kwargs):
        self._target = None
        self.playground = playground
        self.manipulator = manipulator
        super(AdornerBase, self).__init__(size_hint=(None, None), **kwargs)
        self.select(target)
        self.update = Clock.create_trigger(self._update)
        Clock.schedule_interval(self.update, 0)

    def select(self, widget):
        '''Select a target widget to adorn
        '''
        self.target = widget
        self._update()
    
    def on_target(self, _, target):
        if self._target:
            self._target.unbind(pos=self._update, size=self._update)
        self._target = self.target
        if self.target:
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
            pos = self.playground.to_widget(*t.to_window(t.pos[0] * scale, t.pos[1] * scale))
            # self.count = getattr(self, 'count', 0) + 1
            # pos = self.manipulator.to_widget(*t.to_window(*t.pos))
            self.pos = pos
            self.size = t.width * scale, t.height * scale
            self._adorn()
        else:
            self.size = 0, 0
    
    def _adorn(self):
        pass
    
    def prepare_operation(self, touch):
        return None
    
    @classmethod
    def applies_to(cls, widget):
        '''Determines if this adorner should be applied to the given :class:`~kivy.uix.widget.Widget`
        '''
        return False
    
    @property
    def active(self):
        return self.target and self in self.manipulator.active_adorners

class MovingAdorner(AdornerBase):
    # do_reparent = BooleanProperty(True)
    # '''Indicate whether this adorner should reparent the widget
    #    :data:`do_reparent` is a :class:`~kivy.properties.BooleanProperty`
    # '''
    # 
    # do_translate = BooleanProperty(False)
    # '''Indicate whether this adorner should translate the widget
    #    :data:`do_translate` is a :class:`~kivy.properties.BooleanProperty`
    # '''

    moving = ObjectProperty(allownone=True)
    
    parent_outline_alpha = NumericProperty(0.2)
    parent_outline_width = NumericProperty(1.5)
    
    move_operation = ManipulatorTranslateOperation
    
    def __init__(self, **kwargs):
        super(MovingAdorner, self).__init__(**kwargs)
        self.bind(moving=lambda *_: setattr(self, 'highlight', bool(self.moving)))
        
        with self.manipulator.canvas.before:
            self.parent_outline_color = Color(1, 1, 0.2, 0.0)
            self.parent_outline = Line(points=(0, 0), close=True)
        
        anim_in = Animation(parent_outline_alpha=0.6, parent_outline_width=3.5, duration=0.5)
        anim_out = Animation(parent_outline_alpha=0.2, parent_outline_width=1.5, duration=0.5)
        self.anim = anim_in + anim_out
        self.anim.repeat = True
        self.anim.start(self)

    def prepare_operation(self, touch):
        if self.center_area.collide_point(*touch.pos):
            self.moving = self.move_operation(self.target, self.manipulator)
            touch.grab(self)
            return self.moving
        
        return super(MovingAdorner, self).prepare_operation(touch)
    
    def on_touch_up(self, touch):
        if touch.grab_current is self:
            self.moving = None

    def get_outline_area(self):
        parent = self.target.parent
        scale = self.manipulator.playground.scale
        x, y = self.manipulator.playground.to_widget(*parent.to_window(parent.x * scale, parent.y * scale))
        right, top = self.manipulator.playground.to_widget(*parent.to_window(parent.right * scale, parent.top * scale))
        return x, y, right, top

    def _adorn(self):
        if self.moving and self.manipulator.current_adorner is self and self.target and self.target.parent:
            x, y, right, top = self.get_outline_area()
            self.parent_outline_color.a = self.parent_outline_alpha
            self.parent_outline.points = [x, y, right, y, right, top, x, top]
            self.parent_outline.width = self.parent_outline_width
        else:
            self.parent_outline_color.a = 0.0
        super(MovingAdorner, self)._adorn()

class NullAdorner(MovingAdorner):
    move_operation = ManipulatorNullOperation

class RootAdorner(AdornerBase):
    exclusive = True
    
    def __init__(self, **kwargs):
        kwargs['border_color'] = 0, 0, 0, 0
        super(RootAdorner, self).__init__(**kwargs)
    
    @classmethod
    def applies_to(cls, widget):
        return isinstance(widget.parent, SandboxContent)

class PlaygroundDragAdorner(AdornerBase):
    exclusive = True
    
    dragelem = ObjectProperty(allownone=True)
    
    def __init__(self, **kwargs):
        super(PlaygroundDragAdorner, self).__init__(**kwargs)
        self.ids['border_frame'].opacity = 0
    
    # def on_touch_move(self, touch):
    # 	if touch.grab_current is self:
    # 		self.playground.sandbox.error_active = True
    # 		dropelem = None
    # 		
    # 		if isinstance(self.target.parent, PlaygroundDragElement):
    # 			self.dragelem = self.target.parent
    # 		
    # 		if self.target.parent is not self.dragelem:
    # 			return False
    # 		
    # 		reparented = False
    # 		
    # 		with self.playground.sandbox:
    # 			self.dragelem.center_x = touch.x
    # 			self.dragelem.y = touch.y + 20
    # 			
    # 			local = self.playground.to_widget(*touch.pos)
    # 			is_intersecting_playground = self.playground.collide_point(*touch.pos)
    # 			if is_intersecting_playground:
    # 				dropelem = self.playground.try_place_widget(self.target, touch.x, touch.y)
    # 			else:
    # 				pass
    # 			
    # 			if helpers.widget_contains(self.target, dropelem):
    # 				return True
    # 			
    # 			def add_widget(widget, index=0, real=False):
    # 				if self.target.parent:
    # 					if dropelem:
    # 						if isinstance(dropelem, ScreenManager):
    # 							if isinstance(self.target, Screen):
    # 								dropelem.remove_widget(self.target)
    # 							dropelem.real_remove_widget(self.target)
    # 						elif not isinstance(dropelem, TabbedPanel):
    # 							dropelem.remove_widget(self.target)
    # 				
    # 					if self.target.parent:
    # 						self.target.parent.remove_widget(self.target)
    # 				
    # 				if real:
    # 					widget.real_add_widget(self.target, index=index)
    # 				else:
    # 					widget.add_widget(self.target, index=index)
    # 			
    # 			if self.dragelem.drag_type == 'dragndrop':
    # 				can_place = dropelem == self.dragelem.drag_parent
    # 			else:
    # 				can_place = dropelem is not None
    # 			
    # 			self.target.pos = self.dragelem.first_pos
    # 			self.target.pos_hint = self.dragelem.first_pos_hint.copy()
    # 			self.target.size_hint = self.dragelem.first_size_hint
    # 			self.target.size = self.dragelem.first_size
    # 			
    # 			if dropelem:
    # 				if hasattr(dropelem, 'do_layout'):
    # 					dropelem.do_layout()
    # 				if can_place and self.dragelem.drag_type == 'dragndrop':
    # 					if is_intersecting_playground:
    # 						target = self.playground.find_target(local[0], local[1], self.playground.root)
    # 						if target.parent:
    # 							_parent = target.parent
    # 							index = _parent.children.index(target)
    # 							add_widget(dropelem, index)
    # 							reparented = True
    # 					else:
    # 						pass
    # 				elif not can_place and self.target.parent != self.dragelem:
    # 					self.target.pos = 0, 0
    # 					self.target.size_hint = 1, 1
    # 					add_widget(self.dragelem)
    # 				elif can_place and self.dragelem.drag_type != 'dragndrop':
    # 					if isinstance(dropelem, ScreenManager):
    # 						add_widget(dropelem, real=True)
    # 					else:
    # 						add_widget(dropelem)
    # 			elif not can_place and self.target.parent != self.dragelem:
    # 				self.target.pos = 0, 0
    # 				self.target.size_hint = 1, 1
    # 				add_widget(self.dragelem)
    # 		
    # 		if reparented:
    # 			self.on_touch_up(touch)
    # 			if hasattr(dropelem, 'do_layout'):
    # 				dropelem.do_layout()
    # 			self.manipulator.finish_reparent(self.target, touch)
    # 		
    # 		return True
    # 
    # def on_touch_up(self, touch):
    # 	if touch.grab_current is self:
    # 		self.playground.sandbox.error_active = True
    # 		with self.playground.sandbox:
    # 			touch.ungrab(self)
    # 			widget_from = None
    # 			dropelem = None
    # 			local = self.playground.to_widget(*touch.pos)
    # 			is_intersecting_playground = self.playground.collide_point(*touch.pos)
    # 			if is_intersecting_playground:
    # 				dropelem = self.playground.try_place_widget(self.target, touch.x, touch.y)
    # 				widget_from = 'playground'
    # 			else:
    # 				pass
    # 
    # 			if isinstance(self.target.parent, PlaygroundDragElement):
    # 				self.dragelem = self.target.parent
    # 			
    # 			parent = None
    # 			if self.target.parent is not self.dragelem:
    # 				parent = self.target.parent
    # 			elif not self.playground.root:
    # 				parent = self.target.parent
    # 			
    # 			index = -1
    # 			
    # 			if self.dragelem.drag_type == 'dragndrop':
    # 				can_place = dropelem == self.dragelem.drag_parent and parent is not None
    # 			else:
    # 				can_place = dropelem is not None and parent is not None
    # 			
    # 			if dropelem:
    # 				try:
    # 					index = dropelem.children.index(self.target)
    # 				except ValueError:
    # 					pass
    # 				
    # 				dropelem.remove_widget(self.target)
    # 				if isinstance(dropelem, ScreenManager):
    # 					dropelem.real_remove_widget(self.target)
    # 			elif parent:
    # 				index = parent.children.index(self.target)
    # 				parent.remove_widget(self.target)
    # 			
    # 			if can_place or self.playground.root is None:
    # 				target = self.target
    # 				if self.dragelem.drag_type == 'dragndrop':
    # 					if can_place and parent:
    # 						if widget_from == 'playground':
    # 							self.playground.place_widget(target, touch.x, touch.y, index=index)
    # 						else:
    # 							self.playground.place_widget(target, touch.x, touch.y, index=index, target=dropelem)
    # 					elif not can_place:
    # 						self.playground.undo_dragging(touch)
    # 				else:
    # 					if widget_from == 'playground':
    # 						self.playground.place_widget(target, touch.x, touch.y)
    # 					else:
    # 						self.playground.add_widget_to_parent(type(target)(), dropelem)
    # 			elif self.dragelem.drag_type == 'dragndrop':
    # 				self.playground.undo_dragging(touch)
    # 	
    # 	if self.dragelem.parent:
    # 		self.dragelem.parent.remove_widget(self.dragelem)
    # 	
    # 	if self.target in self.dragelem.children:
    # 		self.dragelem.remove_widget(self.target)
    # 		self.dragelem.widgettree.refresh()
    # 	
    # 	return True
    
    def _update(self, *_):
        if self.target:
            self.pos = self.manipulator.to_widget(*self.target.to_window(*self.target.pos))
            self.size = self.target.size
            self._adorn()
        else:
            self.size = 0, 0
            self.dragelem = None
    
    @classmethod
    def applies_to(cls, widget):
        from designer.playground import PlaygroundDragElement
        return isinstance(widget.parent, PlaygroundDragElement)

class BlockAdorner(MovingAdorner):
    move_operation = ManipulatorIndexOperation
    
    move_up_dir = 1
    move_down_dir = -1
    move_left_dir = 1
    move_right_dir = -1
    
    def __init__(self, **kwargs):
        super(BlockAdorner, self).__init__(**kwargs)
        self.bleft = AdornerImageButton(source='icons/appbar.chevron.left.png',
                                        size=self.button_size,
                                        pos_hint={'x': 0, 'center_y': 0.5},
                                        on_press=self.move_left)
        self.bright = AdornerImageButton(source='icons/appbar.chevron.right.png',
                                         size=self.button_size,
                                         pos_hint={'right': 1, 'center_y': 0.5},
                                         on_press=self.move_right)
        self.bup = AdornerImageButton(source='icons/appbar.chevron.up.png',
                                      size=self.button_size,
                                      pos_hint={'center_x': 0.5, 'top': 1},
                                      on_press=self.move_up)
        self.bdown = AdornerImageButton(source='icons/appbar.chevron.down.png',
                                        size=self.button_size,
                                        pos_hint={'center_x': 0.5, 'y': 0},
                                        on_press=self.move_down)
        self.button_area.add_widget(self.bleft)
        self.button_area.add_widget(self.bright)
        self.button_area.add_widget(self.bup)
        self.button_area.add_widget(self.bdown)
    
    def move_left(self, *args):
        self.move(self.move_left_dir)
    
    def move_right(self, *args):
        self.move(self.move_right_dir)
    
    def move_up(self, *args):
        self.move(self.move_up_dir)
    
    def move_down(self, *args):
        self.move(self.move_down_dir)
    
    def refresh_buttons(self, layout):
        pass

    def _adorn(self):
        layout = self.target.parent
        
        self.bleft.disabled = True
        self.bright.disabled = True
        self.bup.disabled = True
        self.bdown.disabled = True
        
        self.highlight = bool(self.moving)
        
        # if self.active and isinstance(layout, BoxLayout) and self.target in layout.children:
        if self.active and self.target in layout.children:
            self.refresh_buttons(layout)
        
        super(BlockAdorner, self)._adorn()

    def move(self, dir, *_):
        parent = self.target.parent
        children = parent.children[:]
        for child in children:
            # print 'remove child', child, child.text
            parent.remove_widget(child)
        idx = children.index(self.target)
        print 'idx', idx
        print 'dest', '0', '<=', str(idx + dir), '<=', str(len(children) - 1)
        print [c.text for c in children]
        dest = max(0, min(idx + dir, len(children) - 1))
        print 'set', idx, 'to', children[dest].text
        children[idx] = children[dest]
        print 'set', dest, 'to', self.target.text
        children[dest] = self.target
        print [c.text for c in children]
        for child in reversed(children):
            # print 'add child', child, child.text
            parent.add_widget(child)


class BoxAdorner(BlockAdorner):
    def get_outline_area(self):
        target = self.target
        parent = target.parent
        x, y, right, top = parent.x, parent.y, parent.right, parent.top
        
        if parent and target in parent.children:
            position = helpers.boxlayout_position(target, parent)
            
            if parent.orientation == 'horizontal':
                if not position['at_front']:
                    x = parent.children[position['layout_pos'] + 1].right
                if not position['at_end']:
                    right = parent.children[position['layout_pos'] - 1].x
            else:
                if not position['at_front']:
                    y = parent.children[position['layout_pos'] + 1].top
                if not position['at_end']:
                    top = parent.children[position['layout_pos'] - 1].y
        
        scale = self.manipulator.playground.scale
        x, y = self.manipulator.playground.to_widget(*parent.to_window(x * scale, y * scale))
        right, top = self.manipulator.playground.to_widget(*parent.to_window(right * scale, top * scale))
        
        return x, y, right, top
    
    def refresh_buttons(self, layout):
        lvals = helpers.boxlayout_position(self.target, layout)
        if layout.orientation == 'horizontal':
            self.bleft.disabled = lvals['at_front']
            self.bright.disabled = lvals['at_end']
        else:
            self.bup.disabled = lvals['at_front']
            self.bdown.disabled = lvals['at_end']
    
    
    @classmethod
    def applies_to(cls, widget):
        return isinstance(widget.parent, BoxLayout)

class GridAdorner(BlockAdorner):
    def get_outline_area(self):
        target = self.target
        parent = target.parent
        x, y, right, top = parent.x, parent.y, parent.right, parent.top
        
        if parent and target in parent.children:
            position = helpers.gridlayout_position(target, parent)
            
            if not position['at_left']:
                # x = parent.children[position['layout_pos'] + 1].right
                x = parent.children[-position['col']].right
            if not position['at_right']:
                # right = parent.children[position['layout_pos'] - 1].x
                right = parent.children[-(position['col'] + 2)].x
            if not position['at_top']:
                # top = parent.children[position['layout_pos'] + position['layout_cols']].y
                top = parent.children[-((position['row'] - 1) * position['layout_cols'] + 1)].y
            if not position['at_bottom']:
                # y = parent.children[position['layout_pos'] - position['layout_cols']].top
                y = parent.children[-((position['row'] + 1) * position['layout_cols'] + 1)].top
        
        scale = self.manipulator.playground.scale
        x, y = self.manipulator.playground.to_widget(*parent.to_window(x * scale, y * scale))
        right, top = self.manipulator.playground.to_widget(*parent.to_window(right * scale, top * scale))
        
        return x, y, right, top
    
    def refresh_buttons(self, layout):
        lvals = helpers.gridlayout_position(self.target, layout)
        self.bleft.disabled = lvals['at_left'] or lvals['at_front']
        self.bright.disabled = lvals['at_right'] or lvals['at_end']
        self.bup.disabled = lvals['at_top'] or lvals['at_front']
        self.bdown.disabled = lvals['at_bottom'] or lvals['at_end']
        
        self.move_up_dir = lvals['layout_cols']
        self.move_down_dir = -lvals['layout_cols']
    
    @classmethod
    def applies_to(cls, widget):
        return isinstance(widget.parent, GridLayout)

class ResizeAdorner(MovingAdorner):
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
        self.icon = 'icons/appbar.arrow.expand.png'
        # self.htop.bind(on_touch_down=self._start_dragging)
        # self.hleft.bind(on_touch_down=self._start_dragging)
        # self.hright.bind(on_touch_down=self._start_dragging)
        # self.hbottom.bind(on_touch_down=self._start_dragging)
        # self.htl.bind(on_touch_down=self._start_dragging)
        # self.htr.bind(on_touch_down=self._start_dragging)
        # self.hbl.bind(on_touch_down=self._start_dragging)
        # self.hbr.bind(on_touch_down=self._start_dragging)
        
        self.htop.pos_hint = {'center_x': 0.5, 'center_y': 1}
        self.hleft.pos_hint = {'center_x': 0, 'center_y': 0.5}
        self.hright.pos_hint = {'center_x': 1, 'center_y': 0.5}
        self.hbottom.pos_hint = {'center_x': 0.5, 'center_y': 0}
        self.htl.pos_hint = {'center_x': 0, 'center_y': 1}
        self.htr.pos_hint = {'center_x': 1, 'center_y': 1}
        self.hbl.pos_hint = {'center_x': 0, 'center_y': 0}
        self.hbr.pos_hint = {'center_x': 1, 'center_y': 0}
        
        self.count = 0
    
    def prepare_operation(self, touch):
        for handle in self.center_area.children:
            if not handle.disabled and handle.collide_point(*touch.pos):
                return ManipulatorResizeOperation(widget=self.target, manipulator=self.manipulator,
                                                  vertical=handle.move_vertical,
                                                  horizontal=handle.move_horizontal)
        return super(ResizeAdorner, self).prepare_operation(touch)
    
    # def _start_dragging(self, handle, touch):
    # 	if handle.disabled:
    # 		return False
    # 	
    # 	if handle.collide_point(*touch.pos):
    # 		touch.grab(self)
    # 		self.resizing = handle
    # 		self.moving_pos = self.playground.to_local(*handle.to_window(*touch.pos))
    # 		self.manipulator.start_resize(self.target, touch)
    # 		return True
    # 
    # def on_touch_move(self, touch):
    # 	if touch.grab_current is self and self.moving_pos:
    # 		pos = self.playground.to_local(*touch.pos)
    # 		dx = pos[0] - self.moving_pos[0]
    # 		dy = pos[1] - self.moving_pos[1]
    # 		self.moving_pos = pos
    # 		
    # 		if self.resizing:
    # 			vertical = self.resizing.move_vertical
    # 			horizontal = self.resizing.move_horizontal
    # 			halign, valign = helpers.get_alignment(self.target)
    # 			
    # 			if vertical != 'none':
    # 				down = vertical == 'down'
    # 				dy = pos[1]
    # 				base_pos = self.target.top if down else self.target.y
    # 				orig_height = self.target.height
    # 				new_height = max(0, (base_pos - dy) if down else (dy - base_pos))
    # 				helpers.resize_widget(self.target, height=new_height)
    # 				real_height = self.target.height
    # 				if self.do_translate:
    # 					orig_y = new_y = self.target.y
    # 					if down and valign == 'bottom':
    # 						new_y += orig_height - real_height
    # 					elif not down and valign == 'top':
    # 						new_y -= orig_height - real_height
    # 					if new_y != orig_y:
    # 						helpers.move_widget(self.target, y=new_y)
    # 				# if down and self.do_translate:
    # 				# 	helpers.move_widget(self.target, y=self.target.y + orig_height - real_height)
    # 			
    # 			if horizontal != 'none':
    # 				left = horizontal == 'left'
    # 				dx = pos[0]
    # 				base_pos = self.target.right if left else self.target.x
    # 				orig_width = self.target.width
    # 				new_width = max(0, (base_pos - dx) if left else (dx - base_pos))
    # 				helpers.resize_widget(self.target, width=new_width)
    # 				real_width = self.target.width
    # 				if self.do_translate:
    # 					orig_x = new_x = self.target.x
    # 					if left and halign == 'left':
    # 						new_x += orig_width - real_width
    # 					elif not left and halign == 'right':
    # 						new_x -= orig_width - real_width
    # 					if new_x != orig_x:
    # 						helpers.move_widget(self.target, x=new_x)
    # 				# if left and self.do_translate:
    # 				# 	helpers.move_widget(self.target, x=self.target.x + orig_width - real_width)
    # 
    # 		return True
    # 
    # def on_touch_up(self, touch):
    # 	if touch.grab_current is self:
    # 		touch.ungrab(self)
    # 		self.resizing = None
    # 		self.moving_pos = 0, 0
    # 		return True
    
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

        # if self.active and isinstance(layout, BoxLayout):
        # 	self.do_translate = False
        # 	enable((self.hbl, self.hbr, self.htl, self.htr, self.htop, self.hbottom, self.hleft, self.hright), False)
        # 	lvals = helpers.BoxLayout.widget_position(self.target, layout)
        # 	if layout.orientation == 'horizontal':
        # 		enable((self.htop,), self.target.valign != 'top')
        # 		enable((self.hbottom,), self.target.valign != 'bottom')
        # 		enable((self.hleft,), not lvals['at_front'])
        # 		enable((self.hright,), not lvals['at_end'])
        # 	else:
        # 		enable((self.hleft,), self.target.halign != 'left')
        # 		enable((self.hright,), self.target.halign != 'right')
        # 		enable((self.htop,), not lvals['at_front'])
        # 		enable((self.hbottom,), not lvals['at_end'])
        # else:
        enable((self.hbl, self.hbr, self.htl, self.htr, self.htop, self.hbottom, self.hleft, self.hright), True)
        # self.do_translate = True
        
        super(ResizeAdorner, self)._adorn()
    
    @classmethod
    def applies_to(cls, widget):
        return isinstance(widget.parent, (FloatLayout,))

class AnchorAdorner(AdornerBase):
    def __init__(self, **kwargs):
        self.atl = Button(text='tl', group='anchor', size_hint=(None, None), 
                                size=self.button_size, pos_hint={'x': 0, 'top': 1})
        self.atop = Button(text='top', group='anchor', size_hint=(None, None), 
                                 size=self.button_size, pos_hint={'center_x': 0.5, 'top': 1})
        self.atr = Button(text='tr', group='anchor', size_hint=(None, None), 
                                size=self.button_size, pos_hint={'right': 1, 'top': 1})
        self.aleft = Button(text='left', group='anchor', size_hint=(None, None), 
                                  size=self.button_size, pos_hint={'x': 0, 'center_y': 0.5})
        self.acenter = Button(text='center', group='anchor', size_hint=(None, None), 
                                    size=self.button_size, pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.aright = Button(text='right', group='anchor', size_hint=(None, None), 
                                   size=self.button_size, pos_hint={'right': 1, 'center_y': 0.5})
        self.abl = Button(text='bl', group='anchor', size_hint=(None, None), 
                                size=self.button_size, pos_hint={'x': 0, 'y': 0})
        self.abottom = Button(text='bottom', group='anchor', size_hint=(None, None), 
                                    size=self.button_size, pos_hint={'center_x': 0.5, 'y': 0})
        self.abr = Button(text='br', group='anchor', size_hint=(None, None), 
                                size=self.button_size, pos_hint={'right': 1, 'y': 0})
        self.afree = Button(text='free', group='anchor', size_hint=(None, None), 
                                  size=self.button_size, pos_hint={'y': 1, 'x': 0.7})
        
        self.halign = self.valign = None
        
        super(AnchorAdorner, self).__init__(**kwargs)
        self.icon = 'icons/appbar.anchor.png'
        
        self.button_area.add_widget(self.atl)
        self.button_area.add_widget(self.atop)
        self.button_area.add_widget(self.atr)
        self.button_area.add_widget(self.aleft)
        self.button_area.add_widget(self.acenter)
        self.button_area.add_widget(self.aright)
        self.button_area.add_widget(self.abl)
        self.button_area.add_widget(self.abottom)
        self.button_area.add_widget(self.abr)
        self.button_area.add_widget(self.afree)
        
        self.atl.bind(on_release=lambda *_: helpers.anchor_widget(self.target, 'x', 'top'))
        self.atop.bind(on_release=lambda *_: helpers.anchor_widget(self.target, 'center_x', 'top'))
        self.atr.bind(on_release=lambda *_: helpers.anchor_widget(self.target, 'right', 'top'))
        self.aleft.bind(on_release=lambda *_: helpers.anchor_widget(self.target, 'x', 'center_y'))
        self.acenter.bind(on_release=lambda *_: helpers.anchor_widget(self.target, 'center_x', 'center_y'))
        self.aright.bind(on_release=lambda *_: helpers.anchor_widget(self.target, 'right', 'center_y'))
        self.abl.bind(on_release=lambda *_: helpers.anchor_widget(self.target, 'x', 'y'))
        self.abottom.bind(on_release=lambda *_: helpers.anchor_widget(self.target, 'center_x', 'y'))
        self.abr.bind(on_release=lambda *_: helpers.anchor_widget(self.target, 'right', 'y'))
        self.afree.bind(on_release=lambda *_: helpers.anchor_widget(self.target, 'free', 'free'))
        
        self._btnmap = {
            'left': {'top': self.atl, 'middle': self.aleft, 'bottom': self.abl},
            'center': {'top': self.atop, 'middle': self.acenter, 'bottom': self.abottom},
            'right': {'top': self.atr, 'middle': self.aright, 'bottom': self.abr}
        }
        
        with self.manipulator.canvas.after:
            self.anchor_indicator_outline_color = Color(1, 0, 0, 1)
            self.anchor_indicator_outline = Ellipse(pos=(0, 0), size=(12, 12))
            self.anchor_indicator_color = Color(0.5, 0, 0, 0.5)
            self.anchor_indicator = Ellipse(pos=(0, 0), size=(10, 10))

    def on_target(self, _, target):
        if self._target:
            self._target.unbind(pos_hint=self._update_anchor, pos=self._update_anchor)
        super(AnchorAdorner, self).on_target(_, target)
        self._target.bind(pos_hint=self._update_anchor, pos=self._update_anchor)
        self._update_anchor()
    
    def _update_anchor(self, *_):
        halign, valign = helpers.get_alignment(self.target)
        
        if halign != self.halign or valign != self.valign:
            # if halign == 'free' or valign == 'free':
            # 	alignbtn = self.afree
            # else:
            # 	alignbtn = self._btnmap[halign][valign]
            # alignbtn._release_group(alignbtn)
            # alignbtn.state = 'down'
            self.halign = halign
            self.valign = valign
    
    def _adorn(self):
        x, y = None, None
        if self.active:
            halign, valign = helpers.get_alignment(self.target)

            if halign == 'left':
                x = 16
            elif halign == 'center':
                x = self.width / 2.
            elif halign == 'right':
                x = self.width - 16

            if valign == 'bottom':
                y = 16
            elif valign == 'middle':
                y = self.height / 2.
            elif valign == 'top':
                y = self.height - 16
            
            # print 'anchor:', halign, valign, x, y
        
        if x is not None and y is not None:
            x, y = self.x + x, self.y + y
            self.anchor_indicator_color.a = 0.5
            self.anchor_indicator_outline_color.a = 1
            self.anchor_indicator.pos = (x - 5, y - 5)
            self.anchor_indicator_outline.pos = (x - 6, y - 6)
        else:
            self.anchor_indicator_color.a = 0
            self.anchor_indicator_outline_color.a = 0
    
    @classmethod
    def applies_to(cls, widget):
        return isinstance(widget.parent, (FloatLayout,))
