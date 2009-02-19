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

from ctypes import c_void_p, c_int64, c_uint64, c_int32, c_uint32, c_int16, c_uint16, c_int8, c_uint8, c_float, c_char, c_char_p, c_wchar, c_wchar_p, HRESULT, POINTER, WINFUNCTYPE, Structure, Union, windll
import winlitecfg

_dll = windll.ntdll

NULL = 0
FALSE = 0
TRUE = 1

VOID = None   # FIXME: ctypes has no concept of the void type
LPCVOID = LPVOID = c_void_p

BOOL = c_int32
LPBOOL = PBOOL = POINTER(BOOL)

BYTE = c_uint8
LPBYTE = PBYTE = POINTER(BYTE)

UCHAR = c_uint8
PUCHAR = POINTER(UCHAR)

WORD = c_uint16
LPWORD = PWORD = POINTER(WORD)

USHORT = c_uint16
PUSHORT = POINTER(USHORT)

INT = c_int32
LPINT = PINT = POINTER(INT)

UINT = c_uint32
PUINT = POINTER(UINT)

FLOAT = c_float
PFLOAT = POINTER(FLOAT)

PSZ = c_char_p

LONG = c_uint32
LPLONG = PLONG = POINTER(LONG)

DWORD = c_uint32
LPDWORD = PDWORD = POINTER(DWORD)

ULONG = c_uint32
PULONG = POINTER(ULONG)

# typed defined in basetsd.h

INT8 = c_int8
PINT8 = POINTER(INT8)
INT16 = c_int16
PINT16 = POINTER(INT16)
INT32 = c_int32
PINT32 = POINTER(INT32)
INT64 = c_int64
PINT64 = POINTER(INT64)
UINT8 = c_uint8
PUINT8 = POINTER(UINT8)
UINT16 = c_uint16
PUINT16 = POINTER(UINT16)
UINT32 = c_uint32
PUINT32 = POINTER(UINT32)
UINT64 = c_uint64
PUINT64 = POINTER(UINT64)
LONG32 = c_int32
PLONG32 = POINTER(LONG32)
ULONG32 = c_uint32
PULONG32 = POINTER(ULONG32)
DWORD32 = c_uint32
PDWORD32 = POINTER(DWORD32)
LONG64 = c_int64
PLONG64 = POINTER(LONG64)
ULONG64 = c_uint64
PULONG64 = POINTER(ULONG64)
DWORD64 = c_uint64
PDWORD64 = POINTER(DWORD64)

INT_PTR = c_int32
PINT_PTR = POINTER(INT_PTR)
UINT_PTR = c_uint32
PUINT_PTR = POINTER(UINT_PTR)
LONG_PTR = c_uint32
PLONG_PTR = POINTER(LONG_PTR)
ULONG_PTR = c_uint32
PULONG_PTR = POINTER(ULONG_PTR)
DWORD_PTR = c_uint32
PDWORD_PTR = POINTER(DWORD_PTR)

MAXINT_PTR = 0x7fffffff
MININT_PTR = 0x80000000
MAXUINT_PTR = 0xffffffff

HALF_PTR = c_int16
PHALF_PTR = POINTER(HALF_PTR)
UHALF_PTR = c_uint16
PUHALF_PTR = POINTER(UHALF_PTR)

MAXUHALF_PTR = 0xffff
MAXHALF_PTR = 0x7fff
MINHALF_PTR = 0x8000

SSIZE_T = LONG_PTR
PSSIZE_T = POINTER(SSIZE_T)
SIZE_T = ULONG_PTR
PSIZE_T = POINTER(SIZE_T)

KAFFINITY = ULONG_PTR
PKAFFINITY = POINTER(KAFFINITY)

# types defined in winnt.h

PVOID = PVOID64 = c_void_p

BOOLEAN = BYTE
PBOOLEAN = POINTER(BOOLEAN)

CHAR = c_char
PCHAR = POINTER(CHAR)

SHORT = c_int16
PSHORT = c_uint16

WCHAR = c_wchar
PWCHAR = POINTER(WCHAR)

LONGLONG = c_int64
PLONGLONG = POINTER(LONGLONG)

ULONGLONG = c_uint64
PULONGLONG = POINTER(ULONGLONG)

DWORDLONG = LONGLONG
PDWORDLONG = POINTER(DWORDLONG)

PCH = LPCH = PCCH = LPCCH = PSTR = LPSTR = NPSTR = PCSTR = LPCSTR = c_char_p
PWCH = LPWCH = PCWCH = LPCWCH = PWSTR = LPWSTR = NPWSTR = PCWSTR = LPCWSTR = c_wchar_p

#to define the neutral char/string types we need the aw setting
winlitecfg.can_set_aw = False
if winlitecfg.aw == 'A':
    TCHAR = CHAR
else:
    TCHAR = WCHAR

PTCHAR = PTSTR = LPTSTR = PCTSTR = LPCTSTR = POINTER(TCHAR)

# TEXT is a macro for converting constant strings on windows, but here a string type will do nicely
TEXT = LPTSTR

CCHAR = c_char

LCID = DWORD
PLCID = POINTER(LCID)

LANGID = WORD

EXECUTION_STATE = DWORD

# HRESULT = ctypes.HRESULT

HANDLE = c_void_p
PHANDLE = LPHANDLE = POINTER(HANDLE)

FCHAR = BYTE
FSHORT = WORD
FLONG = DWORD

class LUID(Structure):
    _fields_ = [
        ('LowPart', DWORD),
        ('HighPart', LONG),
        ]
PLUID = POINTER(LUID)

#end winnt.h types

WPARAM = UINT_PTR
LPARAM = LONG_PTR
LRESULT = LONG_PTR

ATOM = WORD
COLORREF = DWORD
LPCOLORREF = POINTER(DWORD)

HFILE = c_int32
HACCEL = HANDLE
HBITMAP = HANDLE
HBRUSH = HANDLE
HCOLORSPACE = HANDLE
HDC = HANDLE
HDESK = HANDLE
HENHMETAFILE = HANDLE
HFONT = HANDLE
HGLRC = HANDLE
HHOOK = HANDLE
HICON = HANDLE
HINSTANCE = HANDLE
HKEY = HANDLE
PHKEY = POINTER(HKEY)
HKL = HANDLE
HMENU = HANDLE
HMETAFILE = HANDLE
HMONITOR = HANDLE
HPALETTE = HANDLE
HPEN = HANDLE
HRGN = HANDLE
HRSRC = HANDLE
HTASK = HANDLE
HWINEVENTHOOK = HANDLE
HWINSTA = HANDLE
HWND = HANDLE

HMODULE = HINSTANCE
HGDIOBJ = HANDLE
HGLOBAL = HANDLE
HLOCAL = HANDLE
GLOBALHANDLE = HANDLE
LOCALHANDLE = HANDLE
HCURSOR = HICON

FARPROC = WINFUNCTYPE(INT_PTR)
NEARPROC = WINFUNCTYPE(INT_PTR)
PROC = WINFUNCTYPE(INT_PTR)

def LOBYTE(w):
    return w & 0xFF
def HIBYTE(w):
    return (w >> 8)&0xFF

def LOWORD(l):
    return l & 0xFFFF
def HIWORD(l):
    return (l >> 16)&0xFFFF

def MAKEWORD(low, high):
    (low&0xFF) | ((high&0xFF)<<8)

def MAKELONG(low, high):
    (low&0xFFFF) | ((high&0xFFFF)<<16)

MAX_PATH = 260
HFILE_ERROR = -1

class SIZE(Structure):
    _fields_ = [
        ('cx', LONG),
        ('cy', LONG),
        ]
PSIZE = LPSIZE = POINTER(SIZE)

SIZEL = SIZE
PSIZEL = LPSIZEL = POINTER(SIZEL)

class POINT(Structure):
    _fields_ = [
        ('x', LONG),
        ('y', LONG),
        ]
PPOINT = LPPOINT = POINTER(POINT)

class POINTL(Structure):
    _fields_ = [
        ('x', LONG),
        ('y', LONG),
        ]
PPOINTL = POINTER(POINTL)

class POINTS(Structure):
    _fields_ = [
        ('x', SHORT),
        ('y', SHORT),
        ]
PPOINTS = LPPOINTS = POINTER(POINTS)

class FILETIME(Structure):
    _fields_ = [
        ('dwLowDateTime', DWORD),
        ('dwHighDateTime', DWORD),
        ]
PFILETIME = LPFILETIME = POINTER(FILETIME)

class RECT(Structure):
    _fields_ = [
        ('left', LONG),
        ('top', LONG),
        ('right', LONG),
        ('bottom', LONG),
        ]
PRECT = LPRECT = LPCRECT = POINTER(RECT)

class RECTL(Structure):
    _fields_ = [
        ('left', LONG),
        ('top', LONG),
        ('right', LONG),
        ('bottom', LONG),
        ]
PRECTL = LPRECTL = LPCRECTL = POINTER(RECTL)

if winlitecfg.aw == 'W':
    from ctypes import create_unicode_buffer as create_tchar_buffer
else:
    from ctypes import create_string_buffer as create_tchar_buffer

