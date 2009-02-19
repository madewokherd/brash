#Copyright (c) 2008 Vincent Povirk
#
#Permission is hereby granted, free of charge, to any person
#obtaining a copy of this software and associated documentation
#files (the "Software"), to deal in the Software without
#restriction, including without limitation the rights to use,
#copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the
#Software is furnished to do so, subject to the following
#conditions:
#
#The above copyright notice and this permission notice shall be
#included in all copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
#OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
#HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
#WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
#OTHER DEALINGS IN THE SOFTWARE.

"""
winlitecfg module - allows configuration before the bindings are first imported.

To use ANSI, call set_ansi() before importing other modules:

import winlitecfg
winlitecfg.set_ansi()
import winuser
"""

import ctypes

class CfgTooLateError(Exception):
    pass

# ANSI/Unicode setting

can_set_aw = True

def set_unicode():
    """set_unicode - Call before importing other modules to prefer W-suffixed objects
    
    import winlitecfg
    winlitecfg.set_unicode()
    import winuser
    """
    global aw
    if not can_set_aw:
        raise CfgTooLateError("Call winlitecfg.set_unicode() before importing other modules")
    aw = 'W'

def set_ansi():
    """set_ansi - Call before importing other modules to prefer A-suffixed objects
    
    import winlitecfg
    winlitecfg.set_ansi()
    import winuser
    """
    global aw
    if not can_set_aw:
        raise CfgTooLateError("Call winlitecfg.set_ansi() before importing other modules")
    aw = 'A'

if ctypes.windll.kernel32.GetTempPathW(0, 0) == 0 and ctypes.GetLastError() == 120: # 120 == ERROR_CALL_NOT_IMPLEMENTED
    set_ansi()
else:
    set_unicode()

def create_aw_aliases(module_dict):
    """create_aw_aliases(globals())
    
    If nameA and nameW exists but name does not, set name to equal nameA or
    nameW depending on whether ANSI or Unicode is being used.
    """
    global can_set_aw
    if aw == 'W':
        not_aw = 'A'
    else:
        not_aw = 'W'
    for name in module_dict.keys():
        if name.endswith(aw) and name[:-1]+not_aw in module_dict and name[:-1] not in module_dict:
            module_dict[name[:-1]] = module_dict[name]
    can_set_aw = False

def get_aw_symbols(globals, module, names):
    global can_set_aw
    can_set_aw = False
    for name in names:
        globals[name] = getattr(module, name+aw)

#FIXME: define WINVER, _WIN32_IE, _WIN32_WINDOWS, and _WIN32_WINNT

