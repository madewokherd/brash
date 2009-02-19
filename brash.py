#Copyright (c) 2009 Vincent Povirk
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

import os
import sys

_windows = sys.platform == 'win32'

class error(Exception):
    pass

class CommandBlock(object):
    def spawn(self, shell, stdin, stdout, stderr):
        raise NotImplemented

    def poll(self):
        raise NotImplemented

    def wait(self):
        raise NotImplemented

if _windows:
    class ArgBlock(CommandBlock):
        __slots__ = ['_hprocess', '_result', '_args']

        def __init__(self, args):
            self._args = args
        
        def _parse_and_eval_args(self):
            #this has to go
            args = []
            arg = []
            for char in self._args:
                if char.isspace():
                    if arg:
                        args.append(''.join(arg))
                        arg = []
                else:
                    arg.append(char)
            if arg:
                args.append(''.join(arg))
            return args

        def spawn(self, shell, stdin, stdout, stderr):
            args = self._parse_and_eval_args()
            try:
                self._hprocess
            except AttributeError:
                import ctypes, process, subprocess
                cmdline = subprocess.list2cmdline(args)
                si = process.STARTUPINFO()
                pi = process.PROCESS_INFORMATION()
                try:
                    process.CreateProcess(
                        None, #application name
                        cmdline, #command line
                        None, #process attributes
                        None, #thread attributes
                        False, #inherit handles
                        process.CREATE_NEW_PROCESS_GROUP, #flags
                        None, #environment
                        None, #current directory
                        ctypes.byref(si), #startupinfo
                        ctypes.byref(pi), #processinfo
                        )
                except WindowsError, e:
                    import traceback
                    traceback.print_exc()
                    self._hprocess = None
                    self._result = WindowsError.errno
                else:
                    self._hprocess = pi.hProcess
                    ctypes.windll.kernel32.CloseHandle(pi.hThread)
            else:
                raise error("spawn() has already been called")

        def poll(self):
            try:
                return self._result
            except AttributeError:
                import ctypes, process
                if 0 == ctypes.windll.kernel32.WaitForSingleObject(self._hprocess, 0):
                    self._result = process.GetExitCodeProcess(self._hprocess)
                    ctypes.windll.kernel32.CloseHandle(self._hprocess)
                    return self._result
                else:
                    return None

        def wait(self):
            try:
                return self._result
            except AttributeError:
                import ctypes, process
                ctypes.windll.kernel32.WaitForSingleObject(self._hprocess, -1)
                self._result = process.GetExitCodeProcess(self._hprocess)
                ctypes.windll.kernel32.CloseHandle(self._hprocess)
                return self._result
else:
    class ArgBlock(CommandBlock):
        __slots__ = ['_pid', '_result', '_args']

        def __init__(self, args):
            self._args = args

        def _parse_and_eval_args(self):
            args = []
            arg = []
            for char in self._args:
                if char.isspace():
                    if arg:
                        args.append(''.join(arg))
                        arg = []
                else:
                    arg.append(char)
            if arg:
                args.append(''.join(arg))
            return args

        def spawn(self, shell, stdin, stdout, stderr):
            args = self._parse_and_eval_args()
            try:
                self._pid
            except AttributeError:
                pid = os.fork()
                if pid == 0:
                    # child process
                    #FIXME: use PATH and environment from the shell
                    #FIXME: use working dir from the shell
                    #FIXME: use stdin, stdout, and stderr
                    #FIXME: close any other open fd's
                    try:
                        os.execv(args[0], args)
                    except OSError, e:
                        print("%s: %s" % (args[0], e.strerror))
                        os._exit(e.errno)
                    except:
                        import traceback
                        traceback.print_exc()
                        os._exit(1)
                    print("os.execv returned ??!") #shouldn't be possible
                    os._exit(1)
                else:
                    self._pid = pid
            else:
                raise error("spawn() has already been called")

        def poll(self):
            try:
                return self._result
            except AttributeError:
                pid, exitcode = os.waitpid(self._pid, os.WNOHANG)
                if pid:
                    self._result = exitcode
                    return exitcode
                else:
                    return None

        def wait(self):
            try:
                return self._result
            except AttributeError:
                pid, exitcode = os.waitpid(self._pid, 0)
                self._result = exitcode
                return exitcode

class Shell(object):
    def read_input(self):
        return None

    def run(self):
        cmd = self.read_input()
        while cmd is not None:
            block = self.translate_command(cmd)
            block.spawn(self, None, None, None)
            block.wait()
            cmd = self.read_input()

    def translate_command(self, cmd):
        return ArgBlock(cmd)

class InteractiveShell(Shell):
    def read_input(self):
        # TODO: This will need to be written based on curses or something, and we'll need a better prompt
        try:
            return raw_input("$ ")
        except EOFError:
            return None

    def __init__(self):
        self.stdin = sys.stdin
        self.stdout = sys.stdout
        self.stderr = sys.stderr

if __name__ == '__main__':
    InteractiveShell().run()
    print('')

