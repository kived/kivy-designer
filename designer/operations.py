from designer.playground import PlaygroundDragElement
from kivy.uix.boxlayout import BoxLayout

from designer.undo_manager import OperationBase
import designer.helper_functions as helpers
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.tabbedpanel import TabbedPanel


class ManipulatorOperationBase(OperationBase):
    def __init__(self, widget=None, manipulator=None, **kwargs):
        kwargs.setdefault('operation_type', self.__class__.__name__[:-9])
        super(ManipulatorOperationBase, self).__init__(**kwargs)
        self.widget = None
        self.manipulator = manipulator
        self._start = None
        self._finish = None
        
        self._next_operation = None
        
        if widget:
            self.start(widget)

    def _apply(self, state_to):
        pass

    def _apply_kv(self, kvarea, forward=True):
        pass

    def do_undo(self):
        if self._start is not None and self._start != self._finish:
            self._apply(self._start)
            self._apply_kv(self.manipulator.playground.kv_code_input, forward=False)
    
    def do_redo(self):
        if self._start is not None and self._finish is not None and self._start != self._finish:
            self._apply(self._finish)
            self._apply_kv(self.manipulator.playground.kv_code_input)
    
    def get_state(self):
        return {}
    
    def start(self, widget):
        self.widget = widget
        self._start = self.get_state()

    def finish(self):
        self._finish = self.get_state()
        
        return self._finish != self._start
    
    def update(self, touch):
        return self


class ManipulatorTranslateOperation(ManipulatorOperationBase):
    def get_state(self):
        return {#'parent': self.widget.parent,
                #'index': self.widget.parent.children.index(self.widget) if self.widget.parent else None,
                'pos': (self.widget.x, self.widget.y),
                'pos_hint': self.widget.pos_hint.copy(),
                'size': (self.widget.width, self.widget.height),
                'size_hint': (self.widget.size_hint_x, self.widget.size_hint_y)}
    
    def _apply(self, state_to):
        # if self.widget.parent is not state_to['parent']:
        # 	if self.widget.parent:
        # 		self.widget.parent.remove_widget(self.widget)
        # 	state_to['parent'].add_widget(self.widget, state_to['index'])
        self.widget.pos = state_to['pos']
        self.widget.pos_hint = state_to['pos_hint'].copy()
        self.widget.size = state_to['size']
        self.widget.size_hint = state_to['size_hint']
    
    def _apply_kv(self, kvarea, forward=True):
        state_from, state_to = (self._start, self._finish) if forward else (self._finish, self._start)
        # if state_from['parent'] is not state_to['parent']:
        # 	if state_from['parent']:
        # 		kvarea.remove_widget_from_parent(self.widget, state_from['parent'])
        # 	if state_to['parent'] and kvarea._get_widget_path(self.widget):
        # 		kvarea.add_widget_to_parent(self.widget, state_to['parent'])
        # elif isinstance(state_to['parent'], (BoxLayout,)):
        # 	kvarea.shift_widget(self.widget, state_from['index'])
        kvarea.set_property_value(self.widget, 'size_hint', state_to['size_hint'], 'ListProperty')
        if not state_to['size_hint']:
            kvarea.set_property_value(self.widget, 'size', state_to['size'], 'ListProperty')
        kvarea.set_property_value(self.widget, 'pos_hint', state_to['pos_hint'], 'DictProperty')
        if not state_to['pos_hint']:
            kvarea.set_property_value(self.widget, 'pos', state_to['pos'], 'ListProperty')
        # kvarea.refresh(self.manipulator.playground.root)
    
    # def finish(self):
    # 	if super(ManipulatorTranslateOperation, self).finish():
    # 		if self._finish['parent']:
    # 			return True
    # 		self._finish['parent'] = self._start['parent']
    # 	return False
    
    def update(self, touch):
        widget = self.widget
        touch.push()
        touch.apply_transform_2d(self.manipulator.playground.to_widget)
        # print 'widget collides:', widget.collide_point(*touch.pos), ' parent collides:', widget.parent.collide_point(*touch.pos)
        if not widget.parent.collide_point(*touch.pos): # and not widget.collide_point(*touch.pos):
            # print 'do reparent'
            touch.pop()
            return ManipulatorReparentOperation(move_from=self, widget=self.widget, manipulator=self.manipulator, touch=touch)
        else:
            x = widget.x + touch.dx
            y = widget.y + touch.dy
            # print 'move widget', widget, x, y
            helpers.move_widget(widget, x=x, y=y)
            touch.pop()
            return self

class ManipulatorNullOperation(ManipulatorOperationBase):
    def update(self, touch):
        touch.push()
        touch.apply_transform_2d(self.manipulator.playground.to_widget)
        if not self.widget.parent.collide_point(*touch.pos):
            touch.pop()
            return ManipulatorReparentOperation(move_from=self, widget=self.widget, manipulator=self.manipulator, touch=touch)
        return self

class ManipulatorIndexOperation(ManipulatorOperationBase):
    def get_state(self):
        return self.widget.parent.children.index(self.widget)
    
    def _apply(self, state_to):
        parent = self.widget.parent
        parent.remove_widget(self.widget)
        parent.add_widget(self.widget, state_to)
    
    def _apply_kv(self, kvarea, forward=True):
        from_index = (self._start if forward else self._finish)
        print 'move', self.widget, 'from', from_index, 'to', self.widget.parent.children.index(self.widget)
        kvarea.shift_widget(self.widget, from_index)
    
    def finish(self):
        self.widget.parent.do_layout()
        return super(ManipulatorIndexOperation, self).finish()
    
    def update(self, touch):
        widget = self.widget
        parent = widget.parent
        touch.push()
        touch.apply_transform_2d(self.manipulator.playground.to_widget)
        if not parent.collide_point(*touch.pos):
            touch.pop()
            return ManipulatorReparentOperation(move_from=self, widget=self.widget, manipulator=self.manipulator, touch=touch)
        else:
            kw = {}
            do_y = do_x = True
            if isinstance(parent, BoxLayout):
                do_y = parent.orientation == 'vertical'
                do_x = not do_y
            
            if do_y:
                # kw['y'] = widget.y + touch.dy
                kw['y'] = touch.y - widget.height / 2.
            if do_x:
                # kw['x'] = widget.x + touch.dx
                kw['x'] = touch.x - widget.width / 2.
            
            for index, child in enumerate(parent.children):
                if child is not self.widget and child.collide_point(*touch.pos):
                    old_index = parent.children.index(self.widget)
                    # if old_index > index:
                    # 	index -= 1
                    parent.remove_widget(self.widget)
                    parent.add_widget(self.widget, index=index)
                    # print 'children:', parent.children
                    break
            
            helpers.move_widget(widget, **kw)

            touch.pop()
            return self

class ManipulatorReparentOperation(ManipulatorOperationBase):
    def __init__(self, move_from=None, touch=None, **kwargs):
        super(ManipulatorReparentOperation, self).__init__(**kwargs)
        self.move_from = move_from
        self.move_to = None
        self.move_from_parent = self.widget.parent
        self.move_to_parent = None
        self.dragelem = None
        
        self.manipulator.start_reparent(self.widget, touch.x, touch.y)
    
    def __repr__(self):
        return '<%s from=%s to=%s>' % (type(self).__name__, self.move_from, self.move_to)
    
    def do_undo(self):
        super(ManipulatorReparentOperation, self).do_undo()
        if self.move_from:
            self.move_from.do_undo()
    
    def do_redo(self):
        super(ManipulatorReparentOperation, self).do_redo()
        if self.move_to:
            self.move_to.do_redo()
    
    def get_state(self):
        return self.widget.parent
    
    def finish(self):
        super(ManipulatorReparentOperation, self).finish()
        if self.dragelem and self.dragelem.parent:
            self.dragelem.parent.remove_widget(self.dragelem)
        return self.move_to is not None
    
    def _apply(self, state_to):
        if self.widget.parent is not state_to:
            if self.widget.parent:
                self.widget.parent.remove_widget(self.widget)
            if state_to:
                state_to.add_widget(self.widget)
    
    def _apply_kv(self, kvarea, forward=True):
        parent_from, parent_to = (self._start, self._finish) if forward else (self._finish, self._start)
        if parent_from:
            kvarea.remove_widget_from_parent(self.widget, parent_from)
        if parent_to:
            kvarea.add_widget_to_parent(self.widget, parent_to)
    
    def update(self, touch):
        # print 'reparent update', touch, self.widget, self.widget.parent
        
        if isinstance(self.widget.parent, PlaygroundDragElement):
            self.move_to = None
            self.dragelem = self.widget.parent.proxy_ref
            self.dragelem.center_x = touch.x
            self.dragelem.y = touch.y + 20
            
            if self.place_widget(touch):
                x, y = self.manipulator.playground.to_widget(*self.manipulator.to_window(*touch.pos))
                x -= self.widget.width / 2.
                y -= self.widget.height / 2.
                helpers.move_widget(self.widget, x, y)
                # self.manipulator.current_adorner.select(self.widget)
                touch.apply_transform_2d(self.manipulator.current_adorner.center_area.to_widget)
                self.move_to = self.manipulator.current_adorner.prepare_operation(touch)
            
            self.move_to_parent = self.widget.parent
        elif self.move_to:
            self.move_to = self.move_to.update(touch)
            if isinstance(self.move_to, ManipulatorReparentOperation):
                # avoid nesting reparent operations
                self.move_to = None
                self.move_to_parent = None
            
            if self.move_from and self.move_from_parent is self.move_to_parent:
                # drop reparent operation if parent isn't changing
                return self.move_from.update(touch)
        
        return self
    
    def place_widget(self, touch):
        self.manipulator.playground.sandbox.error_active = True
        dropelem = None
        reparented = False
        
        playground = self.manipulator.playground
        
        with playground.sandbox:
            local = playground.to_widget(*touch.pos)
            is_intersecting_playground = playground.collide_point(*touch.pos)
            
            if is_intersecting_playground:
                dropelem = playground.try_place_widget(self.widget, touch.x, touch.y)
            else:
                pass
            
            if helpers.widget_contains(self.widget, dropelem):
                return False
            
            def add_widget(widget, index=0, real=False):
                if self.widget.parent:
                    if dropelem:
                        if isinstance(dropelem, ScreenManager):
                            if isinstance(self.widget, Screen):
                                dropelem.remove_widget(self.widget)
                            dropelem.real_remove_widget(self.widget)
                        elif not isinstance(dropelem, TabbedPanel):
                            dropelem.remove_widget(self.widget)
                    
                    if self.widget.parent:
                        self.widget.parent.remove_widget(self.widget)
                
                if real:
                    widget.real_add_widget(self.widget, index=index)
                else:
                    widget.add_widget(self.widget, index=index)
            
            if self.dragelem.drag_type == 'dragndrop':
                #can_place = dropelem == self.dragelem.drag_parent
                can_place = hasattr(dropelem, 'do_layout')
            else:
                can_place = dropelem is not None
            
            self.widget.pos = self.dragelem.first_pos
            self.widget.pos_hint = self.dragelem.first_pos_hint.copy()
            self.widget.size_hint = self.dragelem.first_size_hint
            self.widget.size = self.dragelem.first_size
            
            if dropelem:
                if hasattr(dropelem, 'do_layout'):
                    dropelem.do_layout()
                if can_place and self.dragelem.drag_type == 'dragndrop':
                    if is_intersecting_playground:
                        target = playground.find_target(local[0], local[1], playground.root)
                        if target.parent:
                            _parent = target.parent
                            index = _parent.children.index(target)
                            add_widget(dropelem, index)
                            reparented = True
                    else:
                        pass
                elif not can_place and self.widget.parent != self.dragelem:
                    self.widget.pos = 0, 0
                    self.widget.size_hint = 1, 1
                    add_widget(self.dragelem)
                elif can_place and self.dragelem.drag_type != 'dragndrop':
                    if isinstance(dropelem, ScreenManager):
                        add_widget(dropelem, real=True)
                    else:
                        add_widget(dropelem)
            elif not can_place and self.widget.parent != self.dragelem:
                self.widget.pos = 0, 0
                self.widget.size_hint = 1, 1
                add_widget(self.dragelem)
            
            if reparented:
                if hasattr(dropelem, 'do_layout'):
                    dropelem.do_layout()
                if self.dragelem.parent:
                    self.dragelem.parent.remove_widget(self.dragelem)
            
            return reparented
    

class ManipulatorResizeOperation(ManipulatorTranslateOperation):
    def __init__(self, vertical=None, horizontal=None, **kwargs):
        super(ManipulatorResizeOperation, self).__init__(**kwargs)
        self.vertical = None if vertical == 'none' else vertical
        self.horizontal = None if horizontal == 'none' else horizontal

    def update(self, touch):
        widget = self.widget
        halign, valign = helpers.get_alignment(widget)
        new_x = None
        new_y = None
        
        touch.apply_transform_2d(self.manipulator.playground.to_widget)
        
        if self.vertical:
            down = self.vertical == 'down'
            base_pos = widget.top if down else widget.y
            orig_height = widget.height
            new_height = max(0, (base_pos - touch.y) if down else (touch.y - base_pos))
            helpers.resize_widget(widget, height=new_height)
            real_height = widget.height
            
            if down and valign == 'bottom':
                new_y = widget.y + orig_height - real_height
            elif not down and valign == 'top':
                new_y = widget.y - orig_height + real_height
        
        if self.horizontal:
            left = self.horizontal == 'left'
            base_pos = widget.right if left else widget.x
            orig_width = widget.width
            new_width = max(0, (base_pos - touch.x) if left else (touch.x - base_pos))
            helpers.resize_widget(widget, width=new_width)
            real_width = widget.width
            
            if left and halign == 'left':
                new_x = widget.x + orig_width - real_width
            elif not left and halign == 'right':
                new_x = widget.x - orig_width + real_width
        
        if new_x or new_y:
            helpers.move_widget(widget, x=None if widget.x == new_x else new_x,
                                y=None if widget.y == new_y else new_y)
        
        return self
    
