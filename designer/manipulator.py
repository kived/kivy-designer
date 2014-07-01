from kivy.event import EventDispatcher
from kivy.properties import ObjectProperty, ListProperty, AliasProperty

from designer.uix.adorner import RootAdorner, PlaygroundDragAdorner, \
    BlockAdorner, ResizeAdorner, AnchorAdorner, AdornerBase
from designer.undo_manager import OperationBase
from kivy.uix.boxlayout import BoxLayout


class ManipulatorMoveOperation(OperationBase):
    def __init__(self, widget=None, manipulator=None):
        super(ManipulatorMoveOperation, self).__init__(operation_type='ManipulatorMove')
        self.widget = None
        self.manipulator = manipulator
        self._start = None
        self._finish = None
        
        if widget:
            self.start(widget)

    def start(self, widget):
        self.widget = widget
        
        start = {'parent': widget.parent,
                 'index': widget.parent.children.index(widget),
                 'pos': (widget.x, widget.y),
                 'pos_hint': widget.pos_hint.copy(),
                 'size': (widget.width, widget.height),
                 'size_hint': (widget.size_hint_x, widget.size_hint_y)}
        self._start = start
    
    def finish(self):
        widget = self.widget
        finish = {'parent': widget.parent,
                  'index': widget.parent.children.index(widget),
                  'pos': (widget.x, widget.y),
                  'pos_hint': widget.pos_hint.copy(),
                  'size': (widget.width, widget.height),
                  'size_hint': (widget.size_hint_x, widget.size_hint_y)}
        self._finish = finish
        
        return self._finish != self._start
    
    def _apply(self, state_to):
        # if state_from and state_from['parent']:
        # 	state_from['parent'].remove_widget(self.widget)
        if self.widget.parent is not state_to['parent']:
            if self.widget.parent:
                self.widget.parent.remove_widget(self.widget)
            state_to['parent'].add_widget(self.widget, state_to['index'])
        self.widget.pos = state_to['pos']
        self.widget.pos_hint = state_to['pos_hint'].copy()
        self.widget.size = state_to['size']
        self.widget.size_hint = state_to['size_hint']
    
    def do_undo(self):
        if self._start:
            self._apply(self._start)
            self._apply_kv(self.manipulator.playground.kv_code_input, forward=False)
    
    def do_redo(self):
        if self._start and self._finish:
            self._apply(self._finish)
            self._apply_kv(self.manipulator.playground.kv_code_input)

    def _apply_kv(self, kvarea, forward=True):
        state_from, state_to = (self._start, self._finish) if forward else (self._finish, self._start)
        if state_from['parent'] is not state_to['parent']:
            if state_from['parent']:
                kvarea.remove_widget_from_parent(self.widget, state_from['parent'])
            if state_to['parent']:
                kvarea.add_widget_to_parent(self.widget, state_to['parent'])
        elif isinstance(state_to['parent'], (BoxLayout,)):
            kvarea.shift_widget(self.widget, state_from['index'])
        kvarea.set_property_value(self.widget, 'size_hint', state_to['size_hint'], 'ListProperty')
        if not state_to['size_hint']:
            kvarea.set_property_value(self.widget, 'size', state_to['size'], 'ListProperty')
        kvarea.set_property_value(self.widget, 'pos_hint', state_to['pos_hint'], 'DictProperty')
        if not state_to['pos_hint']:
            kvarea.set_property_value(self.widget, 'pos', state_to['pos'], 'ListProperty')

class Manipulator(EventDispatcher):
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

    current_adorner = AliasProperty(get_current_adorner, set_current_adorner,
                                    bind=('_current_adorner',))

    adorners = [
        RootAdorner,
        PlaygroundDragAdorner,
        BlockAdorner,
        ResizeAdorner,
        AnchorAdorner,
    ]

    def __init__(self, **kwargs):
        super(Manipulator, self).__init__(**kwargs)
        self.adorners = [a(playground=self.playground, manipulator=self) for a in self.adorners[:]]
        self.null_adorner = AdornerBase(playground=self.playground, manipulator=self)
        self.current_operation = None

    def select(self, widget, touch=None):
        self.target = widget
        if touch:
            self.on_touch_down(touch)

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
    
    def next_adorner(self):
        index = self.active_adorners.index(self.current_adorner) + 1
        if index >= len(self.active_adorners):
            index = 0
        self.current_adorner = self.active_adorners[index]
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
    
    def start_move(self, widget, touch):
        if not ('m_op' in touch.ud and touch.ud['m_op']):
            touch.ud['m_op'] = ManipulatorMoveOperation(widget, self)
    
    def finish_move(self, touch):
        op = touch.ud.get('m_op', None)
        if op:
            if op.finish():
                op.do_redo()
                self.playground.undo_manager.push_operation(op)
            del touch.ud['m_op']
    
    def start_reparent(self, widget, touch):
        pass


__all__ = ['Manipulator']
