from kivy.app import App
from kivy.clock import Clock
from kivy.properties import ObjectProperty, ListProperty, AliasProperty
from designer.uix.adorner import RootAdorner, PlaygroundDragAdorner, \
    BlockAdorner, ResizeAdorner, AnchorAdorner, AdornerBase
from designer.undo_manager import OperationBase
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout


class ManipulatorOperationBase(OperationBase):
    def __init__(self, widget=None, manipulator=None):
        super(ManipulatorOperationBase, self).__init__(operation_type=self.__class__.__name__[:-9])
        self.widget = None
        self.manipulator = manipulator
        self._start = None
        self._finish = None
        
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


class ManipulatorMoveOperation(ManipulatorOperationBase):
    def get_state(self):
        return {'parent': self.widget.parent,
                'index': self.widget.parent.children.index(self.widget) if self.widget.parent else None,
                'pos': (self.widget.x, self.widget.y),
                'pos_hint': self.widget.pos_hint.copy(),
                'size': (self.widget.width, self.widget.height),
                'size_hint': (self.widget.size_hint_x, self.widget.size_hint_y)}
    
    def _apply(self, state_to):
        if self.widget.parent is not state_to['parent']:
            if self.widget.parent:
                self.widget.parent.remove_widget(self.widget)
            state_to['parent'].add_widget(self.widget, state_to['index'])
        self.widget.pos = state_to['pos']
        self.widget.pos_hint = state_to['pos_hint'].copy()
        self.widget.size = state_to['size']
        self.widget.size_hint = state_to['size_hint']
    
    def _apply_kv(self, kvarea, forward=True):
        state_from, state_to = (self._start, self._finish) if forward else (self._finish, self._start)
        if state_from['parent'] is not state_to['parent']:
            if state_from['parent']:
                kvarea.remove_widget_from_parent(self.widget, state_from['parent'])
            if state_to['parent'] and kvarea._get_widget_path(self.widget):
                kvarea.add_widget_to_parent(self.widget, state_to['parent'])
        elif isinstance(state_to['parent'], (BoxLayout,)):
            kvarea.shift_widget(self.widget, state_from['index'])
        kvarea.set_property_value(self.widget, 'size_hint', state_to['size_hint'], 'ListProperty')
        if not state_to['size_hint']:
            kvarea.set_property_value(self.widget, 'size', state_to['size'], 'ListProperty')
        kvarea.set_property_value(self.widget, 'pos_hint', state_to['pos_hint'], 'DictProperty')
        if not state_to['pos_hint']:
            kvarea.set_property_value(self.widget, 'pos', state_to['pos'], 'ListProperty')
        # kvarea.refresh(self.manipulator.playground.root)
    
    def finish(self):
        if super(ManipulatorMoveOperation, self).finish():
            if self._finish['parent']:
                return True
            self._finish['parent'] = self._start['parent']
        return False


class Manipulator(FloatLayout):
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
        self.add_widget(adorner)
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
        Clock.schedule_once(self._setup)
    
    def _setup(self, *_):
        self.adorners = [a(playground=self.playground, manipulator=self) for a in self.adorners[:]]
        self.null_adorner = AdornerBase(playground=self.playground, manipulator=self)
        self.current_operation = None

    def select(self, widget, touch=None):
        self.target = widget
        self.current_adorner.select(self.target)
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
        # else:
        # 	self.current_adorner.select(self.target)
    
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
        if self.current_adorner:
            if self.current_adorner.on_touch_down(touch):
                touch.grab(self)
                return True
    
    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            if 'm_op' in touch.ud:
                self.finish_operation(touch)
    
    def start_move(self, widget, touch):
        if not ('m_op' in touch.ud and touch.ud['m_op']):
            touch.ud['m_op'] = ManipulatorMoveOperation(widget, self)
    
    def start_resize(self, widget, touch):
        if not ('m_op' in touch.ud and touch.ud['m_op']):
            touch.ud['m_op'] = ManipulatorMoveOperation(widget, self)
    
    def finish_operation(self, touch):
        op = touch.ud.get('m_op', None)
        if op:
            if op.finish():
                op.do_redo()
                self.playground.undo_manager.push_operation(op)
            else:
                op.do_undo()
            del touch.ud['m_op']
    
    def start_reparent(self, widget, touch):
        if not ('m_op' in touch.ud and touch.ud['m_op']):
            touch.ud['m_op'] = ManipulatorMoveOperation(widget, self)

        from designer.playground import PlaygroundDragElement

        if not isinstance(widget.parent, PlaygroundDragElement):
            # touch.push()
            # touch.apply_transform_2d(widget.to_window)
            # touch.apply_transform_2d(self.to_widget)
            drag_parent = widget.parent
            widget.parent.remove_widget(widget)
            dragelem = self.create_draggable(widget, touch)
            dragelem.drag_type = 'dragndrop'
            dragelem.drag_parent = drag_parent
            # App.get_running_app().focus_widget(self.target, touch)
            touch.grab(self.current_adorner)
            # touch.pop()
    
    def create_draggable(self, widget, touch):
        from designer.playground import PlaygroundDragElement
        dragelem = PlaygroundDragElement(playground=self.playground, child=widget)
        # touch.grab(dragelem)
        # touch.grab_current = dragelem
        #dragelem.on_touch_move(touch)
        dragelem.center_x = touch.x
        dragelem.y = touch.y + 20
        
        App.get_running_app().root.add_widget(dragelem)
        dragelem.widgettree = self.playground.widgettree
        return dragelem


__all__ = ['Manipulator']
