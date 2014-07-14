'''This file contains a few functions which are required by more than one
   module of Kivy Designer.
'''

__all__ = ['get_indent_str', 'get_line_end_pos', 'get_line_start_pos',
           'get_indent_level', 'get_indentation', 'get_kivy_designer_dir',
           'BoxLayout', 'resize_widget']

import os

from kivy.app import App


def get_indent_str(indentation):
    '''Return a string consisting only indentation number of spaces
    '''
    i = 0
    s = ''
    while i < indentation:
        s += ' '
        i += 1

    return s


def get_line_end_pos(string, line):
    '''Returns the end position of line in a string
    '''
    _line = 0
    _line_pos = -1
    _line_pos = string.find('\n', _line_pos + 1)
    while _line < line:
        _line_pos = string.find('\n', _line_pos + 1)
        _line += 1

    return _line_pos


def get_line_start_pos(string, line):
    '''Returns starting position of line in a string
    '''
    _line = 0
    _line_pos = -1
    _line_pos = string.find('\n', _line_pos + 1)
    while _line < line - 1:
        _line_pos = string.find('\n', _line_pos + 1)
        _line += 1

    return _line_pos


def get_indent_level(string):
    '''Returns the indentation of first line of string
    '''
    lines = string.splitlines()
    lineno = 0
    line = lines[lineno]
    indent = 0
    total_lines = len(lines)
    while line < total_lines and indent == 0:
        indent = len(line)-len(line.lstrip())
        line = lines[lineno]
        line += 1

    return indent


def get_indentation(string):
    '''Returns the number of indent spaces in a string
    '''
    count = 0
    for s in string:
        if s == ' ':
            count += 1
        else:
            return count

    return count


def get_kivy_designer_dir():
    '''This function returns kivy-designer's config dir
    '''
    user_dir = os.path.join(App.get_running_app().user_data_dir,
                            '.kivy-designer')
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)
    return user_dir


def boxlayout_position(widget, layout):
    layout_size = len(layout.children)
    layout_pos = layout.children.index(widget)
    at_front = layout_pos == (layout_size - 1)
    at_end = layout_pos == 0
    return {
        'layout_size': layout_size,
        'layout_pos': layout_pos,
        'at_front': at_front,
        'at_end': at_end
    }


def gridlayout_position(widget, layout):
    layout_size = len(layout.children)
    layout_pos = layout.children.index(widget)
    forward_pos = layout_size - layout_pos - 1
    layout_rows = layout.rows
    layout_cols = layout.cols
    row = col = 0
    at_front = forward_pos == 0
    at_end = forward_pos == (layout_size - 1)
    
    if layout_cols:
        layout_part = layout_size % layout_cols
        layout_rows = layout_size / layout_cols
        if layout_part:
            layout_rows += 1
        row = forward_pos / layout_cols
        col = forward_pos % layout_cols
        # return {
        # 	'layout_size': layout_size,
        #     'layout_pos': layout_pos,
        #     'layout_cols': layout_cols,
        #     'layout_rows': layout_rows,
        #     'row': row,
        # 	'col': col,
        #     'at_top': forward_pos < layout_cols,
        #     'at_bottom': forward_pos >= (layout_size - (layout_size % layout_cols)),
        #     'at_left': forward_pos % layout_cols == 0,
        #     'at_right': forward_pos % layout_cols == layout_cols - 1,
        #     'at_front': at_front,
        #     'at_end': at_end
        # }
    
    elif layout_rows:
        layout_part = layout_size % layout_rows
        layout_cols = layout_size / layout_rows
        if layout_part:
            layout_cols += 1
        row = forward_pos / layout_cols
        col = forward_pos % layout_cols
        # return {
        # 	'layout_size': layout_size,
        #     'layout_pos': layout_pos,
        #     'layout_rows': layout_rows,
        #     'layout_cols': layout_cols,
        #     'row': row,
        #     'col': col,
        #     'at_top': forward_pos % layout_rows == 0,
        #     'at_bottom': forward_pos % layout_rows == layout_rows - 1,
        #     'at_left': forward_pos < layout_cols,
        #     'at_right': forward_pos >= (layout_size - (layout_size % layout_rows)),
        #     'at_front': at_front,
        #     'at_end': at_end
        # }
    
    return {
        'layout_size': layout_size,
        'layout_pos': layout_pos,
        'layout_rows': layout_rows,
        'layout_cols': layout_cols,
        'row': row,
        'col': col,
        'at_top': row == 0,
        'at_bottom': row == layout_rows - 1,
        'at_left': col == 0,
        'at_right': col == layout_cols - 1,
        'at_front': at_front,
        'at_end': at_end
    }


def get_alignment(widget):
    pos_hint = widget.pos_hint
    halign = 'left' if 'x' in pos_hint else (
        'right' if 'right' in pos_hint else ('center' if 'center_x' in pos_hint else 'free'))
    valign = 'top' if 'top' in pos_hint else (
        'bottom' if 'y' in pos_hint else ('middle' if 'center_y' in pos_hint else 'free'))
    return halign, valign


def _resize(widget, size, size_prop, size_hint_prop):
    cur_size_hint = getattr(widget, size_hint_prop)

    if cur_size_hint is None:
        setattr(widget, size_prop, size)
    else:
        cur_size = getattr(widget, size_prop)
        if cur_size_hint < 0.001:
            setattr(widget, size_hint_prop, 1)
            widget.parent.do_layout()
            cur_size = getattr(widget, size_prop)
        ratio = float(size) / cur_size
        size_hint = max(0.001, cur_size_hint * ratio)
        setattr(widget, size_hint_prop, size_hint)


def resize_widget(widget, width=None, height=None):
    if width is not None:
        _resize(widget, width, 'width', 'size_hint_x')

    if height is not None:
        _resize(widget, height, 'height', 'size_hint_y')
    
    widget.parent.do_layout()

def move_widget(widget, x=None, y=None):
    hint = widget.pos_hint.copy()
    if hint:
        parent = widget.parent
        # (x, y) = widget.to_parent(x, y, relative=True)
        if y is not None:
            if 'top' in hint:
                hint['top'] = (y + widget.height) / parent.height
            elif 'center_y' in hint:
                hint['center_y'] = (y + widget.height / 2.) / parent.height
            else:
                hint['y'] = y / parent.height
        
        if x is not None:
            if 'right' in hint:
                hint['right'] = (x + widget.width) / parent.width
            elif 'center_x' in hint:
                hint['center_x'] = (x + widget.width / 2.) / parent.width
            else:
                hint['x'] = x / parent.width
        widget.pos_hint = hint
    else:
        if x is not None:
            widget.x = x
        if y is not None:
            widget.y = y


def _anchor(widget, hint, begin, center, end, size):
    pos_hint = widget.pos_hint.copy()
    if hint and hint not in pos_hint:
        widget_begin = getattr(widget, begin)
        widget_center = getattr(widget, center)
        widget_end = getattr(widget, end)
        parent_size = getattr(widget.parent, size)
        
        new_hint = {}
        
        if hint == begin:
            new_hint[begin] = widget_begin / parent_size
        elif hint == center:
            new_hint[center] = widget_center / parent_size
        elif hint == end:
            new_hint[end] = widget_end / parent_size
        
        if begin in pos_hint:
            del pos_hint[begin]
        if center in pos_hint:
            del pos_hint[center]
        if end in pos_hint:
            del pos_hint[end]
        
        pos_hint.update(new_hint)
        widget.pos_hint = pos_hint


def anchor_widget(widget, hint_x=None, hint_y=None):
    _anchor(widget, hint_x, 'x', 'center_x', 'right', 'width')
    _anchor(widget, hint_y, 'y', 'center_y', 'top', 'height')


def widget_contains(container, child):
    '''Search recursively for child in container
    '''
    if container == child:
        return True
    for w in container.children:
        if widget_contains(w, child):
            return True
    return False
