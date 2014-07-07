from kivy.uix.boxlayout import BoxLayout

from designer.undo_manager import OperationBase
import designer.helper_functions as helpers

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
        if self._start and self._start != self._finish:
            self._apply(self._start)
            self._apply_kv(self.manipulator.playground.kv_code_input, forward=False)
    
    def do_redo(self):
        if self._start and self._finish and self._start != self._finish:
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
        if not widget.parent.collide_point(*touch.pos) and not widget.collide_point(*touch.pos):
            return ManipulatorReparentOperation(move_from=self, widget=self.widget, manipulator=self.manipulator)
        else:
            x = widget.x + touch.dx
            y = widget.y + touch.dy
            print 'move widget', widget, x, y
            helpers.move_widget(widget, x=x, y=y)
            return self

class ManipulatorReparentOperation(ManipulatorOperationBase):
    def __init__(self, move_from=None, **kwargs):
        super(ManipulatorReparentOperation, self).__init__(**kwargs)
        self.move_from = move_from
        self.move_to = None
        

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
    
