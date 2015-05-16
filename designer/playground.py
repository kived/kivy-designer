import re
import functools

from kivy.uix.scatter import ScatterPlane
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.layout import Layout
from kivy.properties import ObjectProperty, BooleanProperty,\
    OptionProperty, ListProperty, NumericProperty
from kivy.app import App
from kivy.metrics import sp
from kivy.uix.filechooser import FileChooserListView, FileChooserIconView
from kivy.uix.floatlayout import FloatLayout
from kivy.factory import Factory
from kivy.base import EventLoop
from kivy.clock import Clock
from kivy.uix.scatterlayout import ScatterLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.carousel import Carousel
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.tabbedpanel import TabbedPanel
from designer.common import widgets
from designer.tree import Tree
from designer.undo_manager import WidgetOperation, WidgetDragOperation
import designer.helper_functions as helpers


class PlaygroundDragElement(BoxLayout):
    '''An instance of this class is the drag element shown when user tries to
       add a widget to :class:`~designer.playground.Playground` by dragging
       from :class:`~designer.toolbox.Toolbox` to
       :class:`~designer.playground.Playground`.
    '''

    playground = ObjectProperty()
    '''Reference to the :class:`~designer.playground.Playground`
       :data:`playground` is a :class:`~kivy.properties.ObjectProperty`
    '''

    target = ObjectProperty(allownone=True)
    '''Widget where widget is to be added.
       :data:`target` a :class:`~kivy.properties.ObjectProperty`
    '''
    can_place = BooleanProperty(False)
    '''Whether widget can be added or not.
       :data:`can_place` is a :class:`~kivy.properties.BooleanProperty`
    '''

    drag_type = OptionProperty('new widget', options=('new widget',
                                                      'dragndrop'))
    '''Specifies the type of dragging currently done by PlaygroundDragElement.
       If it is 'new widget', then it means a new widget will be added
       If it is 'dragndrop', then it means already created widget is
       drag-n-drop, from one position to another.
       :data:`drag_type` is a :class:`~kivy.properties.OptionProperty`
    '''

    drag_parent = ObjectProperty(None)
    '''Parent of currently dragged widget.
       Will be none if 'drag_type' is 'new widget'
       :data:`drag_parent` is a :class:`~kivy.properties.ObjectProperty`
    '''

    placeholder = ObjectProperty(None)
    '''Instance of :class:`~designer.uix.placeholder`
       :data:`placeholder` is a :class:`~kivy.properties.ObjectProperty`
    '''

    widgettree = ObjectProperty(None)
    '''Reference to class:`~designer.nodetree.WidgetsTree`, the widgettree of
       Designer.
       :data:`widgettree` is a :class:`~kivy.properties.ObjectProperty`
    '''

    child = ObjectProperty(None)
    '''The widget which is currently being dragged.
       :data:`child` is a :class:`~kivy.properties.ObjectProperty`
    '''

    def __init__(self, **kwargs):
        super(PlaygroundDragElement, self).__init__(**kwargs)
        self._prev_target = None
        self.i = 0
        if self.child:
            self.first_pos = (self.child.pos[0], self.child.pos[1])
            self.first_pos_hint = self.child.pos_hint.copy()
            self.first_size = (self.child.size[0], self.child.size[1])
            self.first_size_hint = (self.child.size_hint[0],
                                    self.child.size_hint[1])
            self.add_widget(self.child)

    def is_intersecting_playground(self, x, y):
        '''To determine whether x,y is inside playground
        '''
        if not self.playground:
            return False
    
        if self.playground.x <= x <= self.playground.right and\
                self.playground.y <= y <= self.playground.top:
            return True
    
        return False
    
    def is_intersecting_widgettree(self, x, y):
        '''To determine whether x,y is inside playground
        '''
        if not self.widgettree:
            return False
    
        if self.widgettree.x <= x <= self.widgettree.right and\
                self.widgettree.y <= y <= self.widgettree.top:
            return True
    
        return False
    
    def do_layout(self, *largs):
        if not self.child or self.child.parent is not self:
            return
        
        self.child.pos = self.pos
        self.child.size = self.size

    def passoff_to_adorner(self, local, touch):
        self.on_touch_up(touch)
        x, y = local
        x -= self.child.width / 2.
        y -= self.child.height / 2.
        helpers.move_widget(self.child, x, y)
        self.playground.dragging = False
        touch.ud['adorner_passoff'] = True
        App.get_running_app().focus_widget(self.child, touch=touch)

    def on_touch_move(self, touch):
        '''This is responsible for moving the drag element and showing where
           the widget it contains will be added.
        '''
        
        if touch.grab_current is self:
            self.playground.sandbox.error_active = True
            with self.playground.sandbox:
                target = None
                self.center_x = touch.x
                self.y = touch.y + 20
                local = self.playground.to_widget(self.center_x, self.y)
                if self.is_intersecting_playground(self.center_x, self.y):
                    target = self.playground.try_place_widget(
                        self.child, self.center_x, self.y - 20)
        
                else:
                    #self.widgettree.collide_point(self.center_x, self.y)
                    #not working :(
                    #had to use this method
                    if self.is_intersecting_widgettree(self.center_x, self.y):
                        node = self.widgettree.tree.get_node_at_pos(
                            (self.center_x, touch.y))
                        if node:
                            if node.node == self.child:
                                return True
        
                            else:
                                while node and \
                                        node.node != self.playground.sandbox:
                                    widget = node.node
                                    if self.playground.allowed_target_for(
                                            widget, self.child):
                                        target = widget
                                        break
        
                                    node = node.parent_node
        
                if helpers.widget_contains(self.child, target):
                    return True
        
                adorner_passoff = False
        
                def add_widget(target, index=0, real=False):
                    if self.child.parent:
                        if self.target:
                            if isinstance(self.target, ScreenManager):
                                if isinstance(self.child, Screen):
                                    self.target.remove_widget(self.child)
        
                                self.target.real_remove_widget(self.child)
        
                            elif not isinstance(self.target, TabbedPanel):
                                self.target.remove_widget(self.child)
        
                        if self.child.parent:
                            self.child.parent.remove_widget(self.child)
                    
                    if real:
                        target.real_add_widget(self.child, index=index)
                    else:
                        target.add_widget(self.child, index=index)
        
                if self.drag_type == 'dragndrop':
                    self.can_place = target == self.drag_parent
        
                else:
                    self.can_place = target is not None
        
                self.child.pos = self.first_pos
                self.child.pos_hint = self.first_pos_hint.copy()
                self.child.size_hint = self.first_size_hint
                self.child.size = self.first_size
        
                if target:
                    if hasattr(target, 'do_layout'):
                        target.do_layout()
                    if self.can_place and self.drag_type == 'dragndrop':
                        if self.is_intersecting_playground(self.center_x,
                                                           self.y):
                            x, y = self.playground.to_local(*touch.pos)
                            target2 = self.playground.find_target(
                                x, y, self.playground.root)
                            if target2.parent:
                                _parent = target2.parent
                                index = _parent.children.index(target2)
                                add_widget(target, index)
                                if target is not self:
                                    adorner_passoff = True
        
                        else:
                            if self.is_intersecting_widgettree(self.center_x,
                                                               self.y):
                                node = self.widgettree.tree.get_node_at_pos(
                                    (self.center_x, touch.y))
                                if node:
                                    target2 = node.node
                                    if target2.parent:
                                        _parent = target2.parent
                                        add_widget(target, _parent.children.index(target2))
        
                    elif not self.can_place and self.child.parent != self:
                        self.child.pos = (0, 0)
                        self.child.size_hint = (1, 1)
                        add_widget(self)
        
                    elif self.can_place and self.drag_type != 'dragndrop':
                        if isinstance(target, ScreenManager):
                            add_widget(target, real=True)
                        else:
                            add_widget(target)
        
                elif not self.can_place and self.child.parent != self:
                    self.child.pos = (0, 0)
                    self.child.size_hint = (1, 1)
                    add_widget(self)
        
                self.target = target
        
            if adorner_passoff:
                self.passoff_to_adorner(local, touch)
        
        return True

    def on_touch_up(self, touch):
        '''This is responsible for adding the widget to the parent
        '''
        if touch.grab_current is self:
            self.playground.sandbox.error_active = True
            with self.playground.sandbox:
                touch.ungrab(self)
                widget_from = None
                target = None
                self.center_x = touch.x
                self.y = touch.y + 20
                local = self.playground.to_widget(self.center_x, self.y)
                if self.is_intersecting_playground(self.center_x, self.y):
                    target = self.playground.try_place_widget(
                        self.child, self.center_x, self.y - 20)
                    widget_from = 'playground'
        
                else:
                    #self.widgettree.collide_point(self.center_x, self.y)
                    #not working :(
                    #had to use this method
                    if self.is_intersecting_widgettree(self.center_x, self.y):
                        node = self.widgettree.tree.get_node_at_pos(
                            (self.center_x, touch.y))
                        if node:
                            widget = node.node
                            while widget and widget != self.playground.sandbox:
                                if self.playground.allowed_target_for(
                                        widget, self.child):
                                    target = widget
                                    widget_from = 'treeview'
                                    break
        
                                widget = widget.parent
                parent = None
                if self.child.parent != self:
                    parent = self.child.parent
                elif not self.playground.root:
                    parent = self.child.parent
        
                index = -1
        
                if self.drag_type == 'dragndrop':
                    self.can_place = target == self.drag_parent and \
                        parent is not None
                else:
                    self.can_place = target is not None and \
                        parent is not None
        
                if self.target:
                    try:
                        index = self.target.children.index(self.child)
                    except ValueError:
                        pass
        
                    self.target.remove_widget(self.child)
                    if isinstance(self.target, ScreenManager):
                        self.target.real_remove_widget(self.child)
        
                elif parent:
                    index = parent.children.index(self.child)
                    parent.remove_widget(self.child)
        
                if self.can_place or self.playground.root is None:
                    child = self.child
                    if self.drag_type == 'dragndrop':
                        if self.can_place and parent:
                            if widget_from == 'playground':
                                self.playground.place_widget(
                                    child, self.center_x, self.y - 20,
                                    index=index)
                            else:
                                self.playground.place_widget(
                                    child, self.center_x, self.y - 20,
                                    index=index, target=target)
        
                        elif not self.can_place:
                            self.playground.undo_dragging(touch)
        
                        self.playground.drag_operation = []
        
                    else:
                        if widget_from == 'playground':
                            self.playground.place_widget(
                                child, self.center_x, self.y - 20)
        
                        else:
                            #playground.add_widget_to_parent(child,target)
                            #doesn't work, don't know why :/.
                            #so, has to use this
                            self.playground.add_widget_to_parent(type(child)(),
                                                                 target)
        
                elif self.drag_type == 'dragndrop':
                    self.playground.undo_dragging(touch)
        
                self.target = None
        
        if self.parent:
            self.parent.remove_widget(self)
        
        if self.child in self.children:
            self.remove_widget(self.child)
            self.widgettree.refresh()
        
        return True


class Playground(ScatterPlane):
    '''Playground represents the actual area where user will add and delete
       the widgets. It has event on_show_edit, which is emitted whenever
       Playground is clicked.
    '''

    root = ObjectProperty(allownone=True)
    '''This property represents the root widget.
       :data:`root` is a :class:`~kivy.properties.ObjectProperty`
    '''

    selection_mode = BooleanProperty(True)
    '''
       :data:`can_place` is a :class:`~kivy.properties.BooleanProperty`
    '''

    tree = ObjectProperty()

    clicked = BooleanProperty(False)
    '''This property represents whether
       :class:`~designer.playground.Playground` has been clicked or not
       :data:`clicked` is a :class:`~kivy.properties.BooleanProperty`
    '''

    sandbox = ObjectProperty(None)
    '''This property represents the sandbox widget which is added to
       :class:`~designer.playground.Playground`.
       :data:`sandbox` is a :class:`~kivy.properties.ObjectProperty`
    '''

    kv_code_input = ObjectProperty()
    '''This property refers to the
       :class:`~designer.ui_creator.UICreator`'s KVLangArea.
       :data:`kv_code_input` is a :class:`~kivy.properties.ObjectProperty`
    '''

    widgettree = ObjectProperty()
    '''This property refers to the
       :class:`~designer.ui_creator.UICreator`'s WidgetTree.
       :data:`widgettree` is a :class:`~kivy.properties.ObjectProperty`
    '''

    from_drag = BooleanProperty(False)
    '''Specifies whether a widget is dragged or a new widget is added.
       :data:`from_drag` is a :class:`~kivy.properties.BooleanProperty`
    '''

    drag_operation = ListProperty((), allownone=True)
    '''Stores data of drag_operation in form of a tuple.
       drag_operation[0] is the widget which has been dragged.
       drag_operation[1] is the parent of above widget.
       drag_operation[2] is the index of widget in parent's children property.
       :data:`drag_operation` is a :class:`~kivy.properties.ListProperty`
    '''

    _touch_still_down = BooleanProperty(False)
    '''Specifies whether touch is still down or not.
       :data:`_touch_still_down` is a :class:`~kivy.properties.BooleanProperty`
    '''

    dragging = BooleanProperty(False)
    '''Specifies whether currently dragging is performed or not.
       :data:`dragging` is a :class:`~kivy.properties.BooleanProperty`
    '''

    __events__ = ('on_show_edit',)

    def __init__(self, **kwargs):
        super(Playground, self).__init__(**kwargs)
        self.tree = Tree()
        self.keyboard = None
        self.selected_widget = None
        self.undo_manager = None
        self._widget_x = -1
        self._widget_y = -1
        self.widget_to_paste = None

    def on_pos(self, *args):
        '''Default handler for 'on_pos'
        '''
        if self.sandbox:
            self.sandbox.pos = self.pos

    def on_size(self, *args):
        '''Default handler for 'on_size'
        '''
        if self.sandbox:
            self.sandbox.size = self.size

    def on_show_edit(self, *args):
        '''Default handler for 'on_show_edit'
        '''
        pass

    def try_place_widget(self, widget, x, y):
        '''This function is used to determine where to add the widget
        '''

        x, y = self.to_local(x, y)
        return self.find_target(x, y, self.root, widget)

    def place_widget(self, widget, x, y, index=0, target=None):
        '''This function is used to first determine the target where to add
           the widget. Then it add that widget.
        '''
        local_x, local_y = self.to_local(x, y)
        if not target:
            target = self.find_target(local_x, local_y, self.root, widget)

        if not self.from_drag:
            #wx, wy = target.to_widget(x, y)
            #widget.pos = wx, wy
            widget.pos = 0, 0
            self.add_widget_to_parent(widget, target)

        else:
            extra_args = {'x': x, 'y': y, 'index': index}
            self.add_widget_to_parent(widget, target, from_kv=True,
                                      from_undo=True, extra_args=extra_args)

    def drag_wigdet(self, widget, target, extra_args, from_undo=False):
        '''This function will drag widget from one place to another inside
           target
        '''
        extra_args['prev_x'], extra_args['prev_y'] = \
            self.to_parent(self._widget_x, self._widget_y)

        if isinstance(target, FloatLayout) or \
                isinstance(target, ScatterLayout) or \
                isinstance(target, RelativeLayout):
            target.add_widget(widget, self.drag_operation[2])
            widget.pos_hint = {}
            x, y = self.to_local(extra_args['x'],
                                 extra_args['y'])
            self.from_drag = False
            added = True
            local_x, local_y = x - target.x, y - target.y
            hint_x = local_x / target.width
            hint_y = local_y / target.height
            self.kv_code_input.set_property_value(
                widget, 'pos_hint', "{'center_x': %f, 'center_y': %f}" % (
                    hint_x, hint_y),
                'ListPropery')
            widget.pos_hint = {'center_x': hint_x, 'center_y': hint_y}

            if not from_undo:
                self.undo_manager.push_operation(
                    WidgetDragOperation(widget, target,
                                        self.drag_operation[1],
                                        self.drag_operation[2],
                                        self, extra_args=extra_args))

        elif isinstance(target, BoxLayout) or \
                isinstance(target, AnchorLayout) or \
                isinstance(target, GridLayout):
            target.add_widget(widget, extra_args['index'])
            self.from_drag = False
            added = True
            if 'prev_index' in extra_args:
                self.kv_code_input.shift_widget(widget,
                                                extra_args['prev_index'])

            else:
                self.kv_code_input.shift_widget(widget, self.drag_operation[2])

            if not from_undo:
                self.undo_manager.push_operation(
                    WidgetDragOperation(widget, target,
                                        self.drag_operation[1],
                                        self.drag_operation[2],
                                        self, extra_args=extra_args))

    def add_widget_to_parent(self, widget, target, from_undo=False,
                             from_kv=False, kv_str='', extra_args={}):
        '''This function is used to add the widget to the target.
        '''
        added = False
        if target is None:
            with self.sandbox:
                self.root = widget
                self.sandbox.add_widget(widget)
                widget.size = self.sandbox.size
                added = True

        else:
            with self.sandbox:
                if extra_args and self.from_drag:
                    print 'drag_wigdet!', widget, target, extra_args
                    self.drag_wigdet(widget, target, extra_args=extra_args)

                else:
                    target.add_widget(widget)
                    added = True

        if not added:
            return False

        self.widgettree.refresh()

        if not from_kv:
            self.kv_code_input.add_widget_to_parent(widget, target,
                                                    kv_str=kv_str)
        if not from_undo:
            root = App.get_running_app().root
            root.undo_manager.push_operation(WidgetOperation('add',
                                                             widget, target,
                                                             self, ''))

    def get_widget(self, widgetname, **default_args):
        '''This function is used to get the instance of class of name,
           widgetname.
        '''

        widget = None
        with self.sandbox:
            custom = False
            for _widget in widgets:
                if _widget[0] == widgetname and _widget[1] == 'custom':
                    widget = App.get_running_app().root\
                        .project_loader.get_widget_of_class(widgetname)
                    custom = True
            if not custom:
                try:
                    widget = getattr(Factory, widgetname)(**default_args)
                except:
                    pass

        return widget

    def get_playground_drag_element(self, widgetname, touch, **default_args):
        '''This function will return the desired playground element
           for widgetname.
        '''

        widget = self.get_widget(widgetname, **default_args)
        container = PlaygroundDragElement(playground=self, child=widget)
        touch.grab(container)
        container.center_x = touch.x
        container.y = touch.y + 20
        return container

    def cleanup(self):
        '''This function is used to clean the state of Playground, cleaning
           the changes done by currently opened project.
        '''

        #Cleanup is called when project is created or loaded
        #so this operation shouldn't be recorded in Undo
        if self.root:
            self.remove_widget_from_parent(self.root, from_undo=True,
                                           from_kv=True)

        self.tree = Tree()

    def remove_widget_from_parent(self, widget, from_undo=False,
                                  from_kv=False):
        '''This function is used to remove widget its parent.
        '''

        parent = None
        root = App.get_running_app().root
        if not widget:
            return

        removed_str = ''
        if not from_kv:
            removed_str = self.kv_code_input.remove_widget_from_parent(widget,
                                                                       parent)
        if widget != self.root:
            parent = widget.parent
            if isinstance(parent.parent, Carousel):
                parent.parent.remove_widget(widget)

            elif isinstance(parent, ScreenManager):
                if isinstance(widget, Screen):
                    parent.remove_widget(widget)
                else:
                    parent.real_remove_widget(widget)

            else:
                parent.remove_widget(widget)
        else:
            self.root.parent.remove_widget(self.root)
            self.root = None

        #self.tree.delete(widget)
        root.ui_creator.widgettree.refresh()
        if not from_undo:
            root.undo_manager.push_operation(
                WidgetOperation('remove', widget, parent, self, removed_str))

    def find_target(self, x, y, target, widget=None):
        '''This widget is used to find the widget which collides with x,y
        '''
        if target is None:
            return None

        collides = target.collide_point(x, y)

        x, y = target.to_local(x, y)
        class_rules = App.get_running_app().root.project_loader.class_rules

        for child in target.children:
            is_child_custom = False
            for rule in class_rules:
                if rule.name == type(child).__name__:
                    is_child_custom = True
                    break

            is_child_complex = False
            for _widget in widgets:
                if _widget[0] == type(child).__name__ and\
                        _widget[1] == 'complex':
                    is_child_complex = True
                    break

            #if point lies in custom wigdet's child then return custom widget
            if is_child_custom or is_child_complex:
                if not widget and self._custom_widget_collides(child, x, y):
                    return child

                elif widget:
                    if isinstance(child, TabbedPanel):
                        if child.current_tab:
                            _item = self.find_target(
                                x, y, child.current_tab.content)
                            return _item

                    else:
                        return target if collides else None

            elif isinstance(child.parent, Carousel):
                t = self.find_target(x, y, child, widget)
                return t

            else:
                if not self.allowed_target_for(child, widget) and not\
                        child.children:
                    continue

                t = self.find_target(x, y, child, widget)
                if t and t.collide_point(x, y):
                    return t

        return target if collides else None

    def _custom_widget_collides(self, widget, x, y):
        '''This widget is used to find which custom widget collides with x,y
        '''
        if not widget:
            return False

        if widget.collide_point(x, y):
            return True

        x, y = widget.to_local(x, y)
        for child in widget.children:
            if self._custom_widget_collides(child, x, y):
                return True

        return False

    def allowed_target_for(self, target, widget):
        '''This function is used to determine if widget could be added to
           target.
        '''
        # stop on complex widget
        t = target if widget else target.parent
        if isinstance(t, FileChooserListView):
            return False
        if isinstance(t, FileChooserIconView):
            return False

        # stop on custom widget but not root widget
        class_rules = App.get_running_app().root.\
            project_loader.class_rules
        root_widget = App.get_running_app().root.\
            project_loader.root_rule.widget

        # if we don't have widget, always return true
        if widget is None:
            return True

        is_widget_layout = isinstance(widget, Layout)
        is_target_layout = isinstance(target, Layout)
        if is_widget_layout and is_target_layout:
            return True

        if is_target_layout or isinstance(target, Carousel):
            return True

        return False

    def _keyboard_released(self, *args):
        '''Called when self.keyboard is released
        '''
        self.keyboard.unbind(on_key_down=self._on_keyboard_down)
        self.keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        '''Called when a key on keyboard is pressed
        '''
        if modifiers != [] and modifiers[-1] == 'ctrl':
            if keycode[1] == 'c':
                self.do_copy()

            elif keycode[1] == 'v':
                self.do_paste()

            elif keycode[1] == 'x':
                self.do_cut()

            elif keycode[1] == 'a':
                self.do_select_all()

            elif keycode[1] == 'z':
                self.do_undo()

            elif modifiers[0] == 'shift' and keycode[1] == 'z':
                self.do_redo()

        elif keycode[1] == 'delete':
            self.do_delete()

    def do_undo(self):
        '''Undoes the last operation
        '''
        self.undo_manager.do_undo()

    def do_redo(self):
        '''Undoes the last operation
        '''
        self.undo_manager.do_redo()

    def do_copy(self, for_drag=False):
        '''Copy the selected widget
        '''
        base_widget = self.selected_widget
        if base_widget:
            self.widget_to_paste = self.get_widget(type(base_widget).__name__)
            props = base_widget.properties()
            for prop in props:
                if prop == 'id' or prop == 'children':
                    continue

                setattr(self.widget_to_paste, prop,
                        getattr(base_widget, prop))

            self.widget_to_paste.parent = None
            widget_str = self.kv_code_input.\
                get_widget_text_from_kv(base_widget, None)

            if not for_drag:
                widget_str = re.sub(r'\s+id:\s*[\w\d_]+', '', widget_str)
            self._widget_str_to_paste = widget_str

    def do_paste(self):
        '''Paste the selected widget to the current widget
        '''
        parent = self.selected_widget
        if parent and self.widget_to_paste:
            class_rules = App.get_running_app().root.\
                project_loader.class_rules
            root_widget = App.get_running_app().root.\
                project_loader.root_rule.widget
            is_child_custom = False
            for rule in class_rules:
                if rule.name == type(parent).__name__:
                    is_child_custom = True
                    break

            #find appropriate parent to add widget_to_paste
            while parent:
                if isinstance(parent, Layout) and (not is_child_custom
                                                   or root_widget == parent):
                    break

                parent = parent.parent
                is_child_custom = False
                for rule in class_rules:
                    if rule.name == type(parent).__name__:
                        is_child_custom = True
                        break

            if parent is not None:
                self.add_widget_to_parent(self.widget_to_paste,
                                          parent,
                                          kv_str=self._widget_str_to_paste)
                self.widget_to_paste = None

    def do_cut(self):
        '''Cuts the selected widget
        '''
        base_widget = self.selected_widget

        if base_widget and base_widget.parent:
            self.widget_to_paste = base_widget
            self._widget_str_to_paste = self.kv_code_input.\
                get_widget_text_from_kv(base_widget, None)

            self.remove_widget_from_parent(base_widget)

    def do_select_all(self):
        '''Select All widgets which basically means selecting root widget
        '''
        self.selected_widget = self.root
        App.get_running_app().focus_widget(self.root)

    def do_delete(self):
        '''Delete the selected widget
        '''
        if self.selected_widget:
            self.remove_widget_from_parent(self.selected_widget)
            self.selected_widget = None

    def on_touch_move(self, touch):
        '''Default handler for 'on_touch_move'
        '''
        if self.widgettree.dragging is True:
            return True

        super(Playground, self).on_touch_move(touch)
        return False

    def on_touch_up(self, touch):
        '''Default handler for 'on_touch_move'
        '''
        if super(ScatterPlane, self).collide_point(*touch.pos):
            self.dragging = False
            Clock.unschedule(self.start_widget_dragging)
    
        return super(Playground, self).on_touch_up(touch)

    def undo_dragging(self, touch=None):
        '''To undo the last dragging operation if it has not been completed.
        '''
        if touch:
            op = touch.ud.get('m_op', None)
            if op:
                op.do_undo()
                return
        
        if not self.drag_operation:
            return

        if self.drag_operation[0].parent:
            self.drag_operation[0].parent.remove_widget(self.drag_operation[0])

        self.drag_operation[1].add_widget(self.drag_operation[0],
                                          self.drag_operation[2])
        Clock.schedule_once(functools.partial(
                            App.get_running_app().focus_widget,
                            self.drag_operation[0]), 0.01)
        self.drag_operation = []

    def start_widget_dragging(self, *args):
        '''This function will create PlaygroundDragElement
           which will start dragging currently selected widget.
        '''
        if (not self.dragging and # not self.drag_operation and\
                self.selected_widget and self.touch_pos):
            drag_widget = self.selected_widget
            self._widget_x, self._widget_y = drag_widget.x, drag_widget.y
            index = self.selected_widget.parent.children.index(drag_widget)
            self.drag_operation = (drag_widget, drag_widget.parent, index)
    
            self.selected_widget.parent.remove_widget(self.selected_widget)
            drag_elem = App.get_running_app().create_draggable_element(
                '', self.touch, self.selected_widget)
    
            drag_elem.drag_type = 'dragndrop'
            drag_elem.drag_parent = self.drag_operation[1]
            self.dragging = True
            self.from_drag = True
            App.get_running_app().focus_widget(None)

    def prepare_widget_dragging(self, touch, delay=1):
        if not self.dragging:
            self.touch = touch
            self.touch_pos = touch.pos
            Clock.schedule_once(self.start_widget_dragging, delay)

    # def on_touch_down(self, touch):
    # 	'''An override of ScatterPlane's on_touch_down.
    # 	   Used to determine the current selected widget and also emits,
    # 	   on_show_edit event.
    # 	'''
    # 	
    # 	raise RuntimeError()
    # 
    # 	self.touch_pos = None
    # 	if super(ScatterPlane, self).collide_point(*touch.pos) and \
    # 			not self.keyboard:
    # 		win = EventLoop.window
    # 		self.keyboard = win.request_keyboard(self._keyboard_released, self)
    # 		self.keyboard.bind(on_key_down=self._on_keyboard_down)
    # 	
    # 	if self.selection_mode:
    # 		x, y = self.to_local(*touch.pos)
    # 		target = self.find_target(x, y, self.root)
    # 		if target:
    # 			self.selected_widget = target
    # 			App.get_running_app().focus_widget(target, touch=touch)
    # 			self.clicked = True
    # 			self.dispatch('on_show_edit', Playground)
    # 			return True
    # 
    # 	if self.parent.collide_point(*touch.pos):
    # 		super(Playground, self).on_touch_down(touch)
    # 
    # 	return False
