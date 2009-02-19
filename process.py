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

#Process creation/manipulation

from ctypes import windll, Structure, POINTER, byref
from winlitecfg import get_aw_symbols
from winliteutils import get_symbols, NONZERO
from windef import LPCTSTR, LPTSTR, BOOL, DWORD, LPVOID, WORD, LPBYTE, HANDLE, LPDWORD

DEBUG_PROCESS = 0x00000001
DEBUG_ONLY_THIS_PROCESS = 0x00000002
CREATE_SUSPENDED = 0x00000004
DETACHED_PROCESS = 0x00000008
CREATE_NEW_CONSOLE = 0x00000010
CREATE_NEW_PROCESS_GROUP = 0x00000200
CREATE_UNICODE_ENVIRONMENT = 0x00000400
CREATE_SEPARATE_WOW_VDM = 0x00000800
CREATE_SHARED_WOW_VDM = 0x00001000
INHERIT_PARENT_AFFINITY = 0x00010000
CREATE_PROTECTED_PROCESS = 0x00040000
EXTENDED_STARTUPINFO_PRESENT = 0x00080000
CREATE_BREAKAWAY_FROM_JOB = 0x01000000
CREATE_PRESERVE_CODE_AUTHZ_LEVEL = 0x02000000
CREATE_DEFAULT_ERROR_MODE = 0x04000000
CREATE_NO_WINDOW = 0x08000000

class SECURITY_ATTRIBUTES(Structure):
    _fields_ = [
        ("nLength", DWORD),
        ("lpSecurityDescriptor", LPVOID),
        ("bInheritHandle", BOOL),
        ]
PSECURITY_ATTRIBUTES = LPSECURITY_ATTRIBUTES = POINTER(SECURITY_ATTRIBUTES)

class STARTUPINFO(Structure):
    _fields_ = [
        ('cb', DWORD),
        ('lpReserved', LPTSTR),
        ('lpDesktop', LPTSTR),
        ('lpTitle', LPTSTR),
        ('dwX', DWORD),
        ('dwY', DWORD),
        ('dwXSize', DWORD),
        ('dwXCountChars', DWORD),
        ('dwYCountChars', DWORD),
        ('dwFillAttribute', DWORD),
        ('dwFlags', DWORD),
        ('wShowWindow', WORD),
        ('cbReserved2', WORD),
        ('lpReserved2', LPBYTE),
        ('hStdInput', HANDLE),
        ('hStdOutput', HANDLE),
        ('hStdError', HANDLE),
        ]
LPSTARTUPINFO = POINTER(STARTUPINFO)

PPROC_THREAD_ATTRIBUTE_LIST = LPPROC_THREAD_ATTRIBUTE_LIST = LPVOID

class STARTUPINFOEX(STARTUPINFO):
    _fields_ = [
        ('StartupInfo', STARTUPINFO),
        ('lpAttributeList', PPROC_THREAD_ATTRIBUTE_LIST),
        ]

class PROCESS_INFORMATION(Structure):
    _fields_ = [
        ('hProcess', HANDLE),
        ('hThread', HANDLE),
        ('dwProcessId', DWORD),
        ('dwThreadId', DWORD),
        ]
LPPROCESS_INFORMATION = POINTER(PROCESS_INFORMATION)

get_aw_symbols(globals(), windll.kernel32, ['CreateProcess'])

CreateProcess.argtypes = [LPCTSTR, LPTSTR, LPSECURITY_ATTRIBUTES, LPSECURITY_ATTRIBUTES, BOOL, DWORD, LPVOID, LPCTSTR, LPSTARTUPINFO, LPPROCESS_INFORMATION]
CreateProcess.restype = NONZERO

get_symbols(globals(), windll.kernel32, ['GetExitCodeProcess'])

GetExitCodeProcess.argtypes = [HANDLE, LPDWORD]
GetExitCodeProcess.restype = NONZERO
_GetExitCodeProcess = GetExitCodeProcess
def GetExitCodeProcess(handle):
    result = DWORD()
    _GetExitCodeProcess(handle, byref(result))
    return result.value

