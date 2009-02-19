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

from ctypes import GetLastError, WinError

class collapsed_attr(object):
    __fields__ = ['attr', 'subattr']    
    
    def __init__(self, attr, subattr):
        self.attr = attr
        self.subattr = subattr
    
    def __get__(self, instance, owner):
        return getattr(getattr(instance or owner, self.attr), self.subattr)
    
    def __set__(self, instance, value):
        setattr(getattr(instance, self.attr), self.subattr, value)
    
    def __delete__(self, instance):
        delattr(getattr(instance, self.attr), self.subattr)

class WinLiteException(Exception):
    pass

def CheckError():
    "CheckError() - raise a WindowsError if GetLastError() returns a non-zero value"
    err = GetLastError()
    if err:
        raise WinError()

def NONZERO(i):
    if i == 0 and GetLastError() != 0:
        raise WinError()
    return i

def ZERO(i):
    if i != 0 and GetLastError() != 0:
        exc = WinError()
        exc.result = i
        raise exc
    return i

class ERRFLAGS(object):
    __fields__ = ['flags']
    
    def __init__(self, module_dict, prefix):
        self.flags = {}
        for name in module_dict:
            if name.startswith(prefix):
                self.flags[name] = module_dict[name]
    
    def __call__(self, i):
        if i != 0:
            flags = []
            for name in self.flags:
                if self.flags[name] & i:
                    flags.append(name)
            e = WinLiteException('|'.join(flags))
            e.flags = i
            raise e
        return i

def get_symbols(globals, module, names):
    for name in names:
        globals[name] = getattr(module, name)

