from kivy.properties import ObjectProperty, ListProperty, AliasProperty

from designer.operations import ManipulatorTranslateOperation
from designer.playground import Playground
from kivy.app import App
from kivy.clock import Clock
from designer.uix.adorner import RootAdorner, PlaygroundDragAdorner, \
    BlockAdorner, ResizeAdorner, AnchorAdorner, AdornerBase
from kivy.uix.floatlayout import FloatLayout
import designer.helper_functions as helpers


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
        if adorner:
            self.add_widget(adorner)
            adorner.select(self.target)

    current_adorner = AliasProperty(get_current_adorner, set_current_adorner,
                                    bind=('_current_adorner',))
    
    current_operation = ObjectProperty(allownone=True)
    
    adorners = [
        RootAdorner,
        PlaygroundDragAdorner,
        BlockAdorner,
        ResizeAdorner,
        AnchorAdorner,
    ]

    def __init__(self, **kwargs):
        super(Manipulator, self).__init__(**kwargs)
        self.keyboard = None
        
        Clock.schedule_once(self._setup)
    
    def _setup(self, *_):
        self.adorners = [a(playground=self.playground, manipulator=self) for a in self.adorners[:]]
        self.null_adorner = AdornerBase(playground=self.playground, manipulator=self)
        self.current_operation = None

    def select(self, widget, touch=None):
        if self.target is widget and self.current_adorner:
            self.current_adorner.select(self.target)
        else:
            self.target = widget
        if touch:
            raise RuntimeError()
            self.on_touch_down(touch)

    def on_target(self, *_):
        if self.target:
            self.target.bind(parent=self.update_adorners)
        self.update_adorners()

    def update_adorners(self, *_):
        if self.target:
            adorners = self._get_adorners_for(self.target)
            if adorners != self.active_adorners:
                self.active_adorners = adorners
                self.current_adorner = self.active_adorners[0]
            self.current_adorner.select(self.target)
        else:
            self.active_adorners = []
            self.current_adorner = None
    
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

    def _keyboard_released(self, *_):
        pass
    
    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        pass

    def on_touch_down(self, touch):
        if self.disabled:
            return False
        
        if not self.keyboard and self.collide_point(*touch.pos):
            self.keyboard = self.get_root_window().request_keyboard(self._keyboard_released, self)
            self.keyboard.bind(on_key_down=self._on_keyboard_down)
        
        assert self.current_operation is None, 'dangling operation %r' % (self.current_operation,)
        
        if self.current_adorner:
            if self.current_adorner.on_touch_down(touch):
                return True
            
            touch.push()
            touch.apply_transform_2d(self.current_adorner.to_widget)
            self.current_operation = self.current_adorner.prepare_operation(touch)
            touch.pop()
        
        if self.current_operation:
            touch.grab(self)
            return True

        x, y = self.playground.to_local(*touch.pos)
        target = self.playground.find_target(x, y, self.playground.root)
        print 'target', target, x, y
        self.select(target)
        self.playground.dispatch('on_show_edit', Playground)

        # if self.current_adorner.on_touch_down(touch):
            # 	touch.grab(self)
            # 	return True
    
    def on_touch_move(self, touch):
        # if touch.grab_current is self and self.current_adorner:
        # 	return self.current_adorner.on_touch_move(touch)
        if touch.grab_current is self and self.current_operation:
            touch.push()
            touch.apply_transform_2d(self.playground.to_local)
            self.current_operation = self.current_operation.update(touch)
            touch.pop()
            return True
    
    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            if self.current_operation:
                if self.current_operation.finish():
                    self.current_operation.do_redo()
                    self.playground.undo_manager.push_operation(self.current_operation)
                else:
                    self.current_operation.do_undo()
                self.current_operation = None
            return True
            # if 'm_op' in touch.ud:
            # 	self.finish_operation(touch)
    
    # def start_move(self, widget, touch):
    # 	if not ('m_op' in touch.ud and touch.ud['m_op']):
    # 		touch.ud['m_op'] = ManipulatorMoveOperation(widget, self)
    # 
    # def start_resize(self, widget, touch):
    # 	if not ('m_op' in touch.ud and touch.ud['m_op']):
    # 		touch.ud['m_op'] = ManipulatorMoveOperation(widget, self)
    # 
    # def finish_operation(self, touch):
    # 	op = touch.ud.get('m_op', None)
    # 	if op:
    # 		if op.finish():
    # 			op.do_redo()
    # 			self.playground.undo_manager.push_operation(op)
    # 		else:
    # 			op.do_undo()
    # 		del touch.ud['m_op']
    
    def start_reparent(self, widget, touch):
        if not ('m_op' in touch.ud and touch.ud['m_op']):
            touch.ud['m_op'] = ManipulatorTranslateOperation(widget, self)

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
            touch.grab_current = self.current_adorner
            self.current_adorner.update()
            self.current_adorner.on_touch_move(touch)
            # touch.pop()
    
    def finish_reparent(self, widget, touch):
        local = self.playground.to_widget(*touch.pos)
        x = local[0] - widget.width / 2.
        y = local[1] - widget.height / 2.
        helpers.move_widget(widget, x, y)
        self.current_adorner.select(widget)
        touch.apply_transform_2d(self.current_adorner.center_area.to_widget)
        self.current_adorner.on_center_touch_down(self.current_adorner.center_area, touch, dispatch_children=False)
    
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
