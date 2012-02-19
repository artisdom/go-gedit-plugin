# -*- coding: utf-8 -*-

# Maximum length of error messages in dialogs.
MAX_ERR_MSG_LEN = 500

def get_iter_cursor(buffer):
    cursor_position = buffer.get_property('cursor-position')
    return buffer.get_iter_at_offset(cursor_position)

def scroll_to_insert(buffer, view):
    insert = buffer.get_insert()
    view.scroll_to_mark(insert, 0.0, True)
