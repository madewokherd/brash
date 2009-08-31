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
import stat
try:
    import thread
except ImportError:
    import _thread

_windows = sys.platform == 'win32'

class error(Exception):
    pass

def expanduser(string, shell):
    # FIXME: os.path uses the current environment, not that of the shell
    return os.path.expanduser(string)

class CommandBlock(object):
    def spawn(self, shell, stdin, stdout, stderr):
        raise NotImplemented

    def poll(self):
        raise NotImplemented

    def wait(self):
        raise NotImplemented

def command_cd(args, shell, stdin, stdout, stderr):
    if len(args) > 1:
        newpath = os.path.normpath(os.path.join(shell.curdir, args[1]))
    else:
        newpath = expanduser('~', shell)
    try:
        st = os.stat(newpath)
    except OSError, e:
        print('cd: %s\n' % e.strerror)
        return e.errno
    else:
        if stat.S_ISDIR(st.st_mode):
            shell.curdir = newpath
            return 0
        else:
            print('cd: %s' % 'Not a directory\n')
            return 1

builtin_commands = {
    'cd': command_cd,
    }

def expr_pwd(shell):
    return [shell.curdir]

def expr_home(shell):
    return [expanduser('~', shell)]

builtin_exprs = {
    'pwd': expr_pwd,
    'home': expr_home,
    }

if _windows:
    class ArgBlock(CommandBlock):
        __slots__ = ['_hprocess', '_result', '_args']

        def __init__(self, args):
            self._args = args

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
                    #FIXME: use PATH and environment from the shell
                    #FIXME: use working dir from the shell
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

    import UserDict
    # the environment needs to be case-insensitive on Windows, case-sensitive on other platforms
    class EnvironDictionary(UserDict.DictMixin):
        def __init__(self, *args, **kwargs):
            if args:
                try:
                    for kv in args[0].iteritems():
                        self.values[kv[0].lower] = kv
                except AttributeError:
                    for kv in args[0]:
                        self.values[kv[0].lower] = kv
            for kv in kwargs.iteritems():
                self.values[kv[0].lower] = kv
        def copy(self):
            return EnvironDictionary(self)
        def __getitem__(self, key):
            return self.values[key.lower()][1]
        def __setitem__(self, key, value):
            self.values[key.lower()] = (key, value)
        def __delitem__(self, key):
            del self.values[key.lower()]
        def keys(self):
            return [x[0] for x in self.values.itervalues()]
        def __contains__(self, key):
            return key.lower() in self.values
        def __iter__(self):
            return (x[0] for x in self.values.itervalues())
        def iteritems(self):
            return self.values.itervalues()
else:
    class ArgBlock(CommandBlock):
        __slots__ = ['_pid', '_result', '_args', '_lock']

        def __init__(self, args):
            self._args = args

        def thread_func(self, command_func, args, shell, stdin, stdout, stderr):
            try:
                self._result = command_func(args, shell, stdin, stdout, stderr)
            except:
                import traceback
                print('An internal error occurred:\n%s' % traceback.print_exc())
                self._result = 31335
            self._lock.release()

        def spawn(self, shell, stdin, stdout, stderr):
            args = shell._parse_and_eval_args(self._args)
            try:
                self._pid
            except AttributeError:
                try: # is this a builtin?
                    command_func = builtin_commands[args[0]]
                except KeyError: #nope
                    pass
                else: #yep
                    self._pid = None
                    self._lock = thread.allocate_lock()
                    self._lock.acquire()
                    #FIXME: get stdin, stdout, and stderr from the shell if necessary
                    thread.start_new_thread(self.thread_func, (command_func, args, shell, stdin, stdout, stderr))
                    return
                pid = os.fork()
                if pid == 0:
                    # child process
                    #FIXME: use stdin, stdout, and stderr
                    #FIXME: close any other open fd's
                    os.chdir(shell.curdir)
                    try:
                        if os.sep in args[0] or (os.altsep and os.altsep in args[0]):
                            # path specifies a directory
                            os.execve(args[0], args, shell.environ)
                        else:
                            # we need to search PATH
                            for path in shell.environ.get('PATH', os.defpath).split(os.pathsep):
                                try:
                                    os.execve(os.path.join(path, args[0]), args, shell.environ)
                                except OSError, e:
                                    if e.errno != 2: #2 is no such file or directory
                                        raise
                            else:
                                print("%s: %s" % (args[0], e.strerror))
                                os._exit(e.errno)
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
                if self._pid:
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
                if self._pid:
                    pid, exitcode = os.waitpid(self._pid, 0)
                    self._result = exitcode
                    return exitcode
                else:
                    self._lock.acquire()
                    self._lock.release()
                    return self._result

    EnvironDictionary = dict

class Shell(object):
    def __init__(self, curdir=None, environ=None):
        if curdir is None:
            curdir = os.getcwd()
        if environ is None:
            environ = EnvironDictionary(os.environ)
        self.curdir = curdir
        self.environ = environ

    def _parse_and_eval_args(self, string):
        # this has to go
        args = []
        arg = []
        i = iter(string)
        while True:
            try:
                char = i.next()
            except StopIteration:
                break
            if char.isspace():
                if arg:
                    args.append(''.join(arg))
                    arg = []
            elif char == '$':
                try:
                    nextchar = i.next()
                except StopIteration:
                    raise SyntaxError("unexpected end of line")
                if nextchar == '$':
                    arg.append('$')
                elif nextchar.isspace():
                    raise SyntaxError("unexpected whitespace")
                else:
                    expr = [nextchar]
                    while True:
                        try:
                            nextchar = i.next()
                        except StopIteration:
                            break
                        if nextchar.isspace():
                            break
                        expr.append(nextchar)
                    expr = ''.join(expr)
                    try:
                        expr_func = builtin_exprs[expr]
                    except KeyError:
                        result = []
                    else:
                        result = expr_func(self)
                    if result:
                        args.append('%s%s' % (''.join(arg), result[0]))
                        args.extend(result[1:])
                        arg = []
                    elif arg:
                        # because we consumed a space earlier, we still have to clear arg
                        args.append(''.join(arg))
                        arg = []
            else:
                arg.append(char)
        if arg:
            args.append(''.join(arg))
        return args

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
            return raw_input("%s> " % self.curdir)
        except EOFError:
            return None

    def __init__(self, *args, **kwargs):
        Shell.__init__(self, *args, **kwargs)
        self.stdin = sys.stdin
        self.stdout = sys.stdout
        self.stderr = sys.stderr

def main():
    curdir = os.getcwd()
    environ = EnvironDictionary(os.environ)
    if not _windows:
        #Since a shell's working directory isn't the process's working directory,
        # we shouldn't keep it open as the current directory
        os.chdir('/')
    shell = InteractiveShell(curdir, environ)
    shell.run()
    print ''

if __name__ == '__main__':
    main()

