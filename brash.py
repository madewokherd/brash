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

def command_cd(args, shell, stdin, stdout, stderr):
    if len(args) > 1:
        newpath = os.path.normpath(os.path.join(shell.curdir, args[1]))
    else:
        newpath = expanduser('~', shell)
    try:
        st = os.stat(newpath)
    except OSError, e:
        stderr.write('cd: %s\n' % e.strerror)
        return e.errno
    else:
        if stat.S_ISDIR(st.st_mode):
            try:
                shell.chdir(newpath)
                return 0
            except OSError, e:
                stderr.write('cd: %s\n' % e.strerror)
                return e.errno
        else:
            stderr.write('cd: %s' % 'Not a directory\n')
            return 1

builtin_commands = {
    'cd': command_cd,
    }

def expr_pwd(shell, stdin, stdout, stderr):
    return [shell.curdir]

def expr_home(shell, stdin, stdout, stderr):
    return [expanduser('~', shell)]

builtin_exprs = {
    'pwd': expr_pwd,
    'home': expr_home,
    }

if _windows:
    class ArgBlock(CommandBlock):
        __slots__ = ['_hprocess', '_result', '_args', '_shell', '_stdin', '_stdout', '_stderr']

        def __init__(self, args, shell, stdin, stdout, stderr, ownfds=()):
            self._args = args
            self._stdin = stdin
            self._stdout = stdout
            self._stderr = stderr
            self._ownfds = ownfds

        def spawn(self):
            try:
                self._hprocess
            except AttributeError:
                import ctypes, process, subprocess
                cmdline = subprocess.list2cmdline(self._args)
                si = process.STARTUPINFO()
                pi = process.PROCESS_INFORMATION()
                try:
                    #FIXME: use PATH and environment from the shell
                    #FIXME: use working dir from the shell
                    #FIXME: use pipes from the shell
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

        def run(self):
            self.spawn()
            return self.wait()

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
    try:
        MAXFD = os.sysconf("SC_OPEN_MAX")
    except:
        MAXFD = 256

    class ExternalCommandInstance(object):
        __slots__ = ['_pid', '_result', '_args', '_lock', '_shell', '_stdin', '_stdout', '_stderr', '_ownfds']

        def __init__(self, args, shell, stdin, stdout, stderr, ownfds=()):
            self._args = args
            self._shell = shell
            self._stdin = stdin
            self._stdout = stdout
            self._stderr = stderr
            self._ownfds = ownfds

        def spawn(self):
            args = self._args
            if not args:
                self._pid = None
                self._result = 0
                return
            try:
                self._pid
            except AttributeError:
                pid = os.fork()
                if pid == 0:
                    # child process
                    # set up streams
                    if self._stdin.fileno() != 0:
                        try:
                            os.close(0)
                        except:
                            pass
                        os.dup2(self._stdin.fileno(), 0)
                    if self._stdout.fileno() != 1:
                        try:
                            os.close(1)
                        except:
                            pass
                        os.dup2(self._stdout.fileno(), 1)
                    # close any other open fd's
                    if self._stderr.fileno() != 2:
                        try:
                            os.close(2)
                        except:
                            pass
                        os.dup2(self._stderr.fileno(), 2)
                    try:
                        os.closerange(3, MAXFD)
                    except AttributeError:
                        for i in xrange(3, MAXFD):
                            try:
                                os.close(i)
                            except:
                                pass
                    os.chdir(self._shell.curdir)
                    try:
                        if os.sep in args[0] or (os.altsep and os.altsep in args[0]):
                            # path specifies a directory
                            os.execve(args[0], args, self._shell.environ)
                        else:
                            # we need to search PATH
                            for path in self._shell.environ.get('PATH', os.defpath).split(os.pathsep):
                                try:
                                    os.execve(os.path.join(path, args[0]), args, self._shell.environ)
                                except OSError, e:
                                    if e.errno != 2: #2 is no such file or directory
                                        raise
                            else:
                                os.write(2, "%s: %s" % (args[0], e.strerror))
                                os._exit(e.errno)
                    except OSError, e:
                        os.write(2, "%s: %s" % (args[0], e.strerror))
                        os._exit(e.errno)
                    except:
                        import traceback
                        self._stderr.write(traceback.format_exc())
                        os._exit(1)
                    os.write(2, "os.execv returned ??!") #shouldn't be possible
                    os._exit(1)
                else:
                    self._pid = pid
                    for fd in self._ownfds:
                        fd.close()
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

        def run(self):
            self.spawn()
            return self.wait()

    EnvironDictionary = dict

class BuiltinActionInstance(object):
    def __init__(self, shell, stdin, stdout, stderr, ownfds=()):
        self._shell = shell
        self._stdin = stdin
        self._stdout = stdout
        self._stderr = stderr
        self._lock = thread.allocate_lock()
        self._lock.acquire()
        self._ownfds = ownfds

    def run(self):
        try:
            self._result = self.work()
        except:
            import traceback
            print('An internal error occurred:\n%s' % traceback.print_exc())
            self._result = 31335
        self._lock.release()
        return self._result

    def spawn(self):
        #FIXME: get stdin, stdout, and stderr from the shell if necessary
        thread.start_new_thread(self.run, ())

    def poll(self):
        try:
            return self._result
        except AttributeError:
            return None

    def wait(self):
        try:
            return self._result
        except AttributeError:
            self._lock.acquire()
            self._lock.release()
            return self._result

class BuiltinCommandInstance(BuiltinActionInstance):
    def __init__(self, command_func, args, *rest, **kwargs):
        BuiltinActionInstance.__init__(self, *rest, **kwargs)
        self._command_func = command_func
        self._args = args

    def work(self):
        try:
            result = self._command_func(self._args, self._shell, self._stdin, self._stdout, self._stderr)
        finally:
            for fd in self._ownfds:
                fd.close()

class DoNothingCommandInstance(object):
    def spawn(self):
        pass
    def poll(self):
        return 0
    def wait(self):
        return 0
    def run(self):
        return 0

class PipelineInstance(BuiltinCommandInstance):
    def __init__(self, blocks, *args, **kwargs):
        BuiltinActionInstance.__init__(self, *args, **kwargs)
        self._blocks = blocks

    def work(self):
        instances = []
        for n, block in enumerate(self._blocks):
            if n == 0:
                r = self._stdin
                _ownfds = []
                if self._stdin in self._ownfds:
                    self._ownfds.remove(self._stdin)
                    _ownfds.append(self._stdin)
            else:
                r = next_r
                _ownfds = [r]
            if n == len(self._blocks)-1:
                w = self._stdout
                if self._stdout in self._ownfds:
                    self._ownfds.remove(self._stdout)
                    _ownfds.append(self._stdout)
            else:
                next_r, w = os.pipe()
                next_r = os.fdopen(next_r, 'r', 0)
                w = os.fdopen(w, 'w', 0)
                _ownfds.append(w)
            instance = block.create_instance(self._shell, r, w, self._stderr, _ownfds)
            instances.append(instance)
            instance.spawn()
        for instance in instances:
            result = instance.wait()
        for fd in self._ownfds:
            fd.close()
        return result

class CommandSequenceInstance(BuiltinCommandInstance):
    def __init__(self, blocks, *args, **kwargs):
        BuiltinActionInstance.__init__(self, *args, **kwargs)
        self._blocks = blocks

    def work(self):
        for n, block in enumerate(self._blocks):
            if n == len(self._blocks)-1:
                ownfds = self._ownfds
            else:
                ownfds = ()
            instance = block.create_instance(self._shell, self._stdin, self._stdout, self._stderr, self._ownfds)
            result = instance.run()
        return result

def eval_args(args, shell, stdin, stdout, stderr):
    result = []
    for arglist in args:
        if not isinstance(arglist, list):
            arglist = arglist(shell, stdin, stdout, stderr)
        if not result or not arglist:
            result.extend(arglist)
        else:
            result[-1] = '%s%s' % (result[-1], arglist[0])
            result.extend(arglist[1:])
    return result

class CommandBlock(object):
    __slots__ = ['args', 'slow']

    def __init__(self, args, slow):
        self.args = args
        self.slow = slow

    def create_instance(self, shell, stdin, stdout, stderr, ownfds=()):
        # FIXME: spawn a thread or something if self.slow
        args = eval_args(self.args, shell, stdin, stdout, stderr)   
        if not args:
            for fd in ownfds:
                fd.close()
            return DoNothingCommandInstance()
        try:
            command_func = builtin_commands[args[0]]
        except KeyError:
            return ExternalCommandInstance(args, shell, stdin, stdout, stderr, ownfds)
        else:
            return BuiltinCommandInstance(command_func, args, shell, stdin, stdout, stderr, ownfds)

class EmptyBlock(object):
    def create_instance(self, shell, stdin, stdout, stderr, ownfds=()):
        for fd in ownfds:
            fd.close()
        return DoNothingCommandInstance()

class PipelineBlock(object):
    __slots__ = ['blocks']

    def __init__(self, blocks):
        self.blocks = blocks

    def create_instance(self, shell, stdin, stdout, stderr, ownfds=()):
        return PipelineInstance(self.blocks, shell, stdin, stdout, stderr, ownfds)

class CommandSequenceBlock(object):
    __slots__ = ['blocks']

    def __init__(self, blocks):
        self.blocks = blocks

    def create_instance(self, shell, stdin, stdout, stderr, ownfds=()):
        return CommandSequenceInstance(self.blocks, shell, stdin, stdout, stderr, ownfds)

_variable_expr_cache = {}

def get_variable_expr(name):
    if name in _variable_expr_cache:
        return _variable_expr_cache[name]
    else:
        def variable_expr(shell, stdin, stdout, stderr):
            try:
                expr_func = builtin_exprs[name]
            except KeyError:
                return ['']
            return expr_func(shell, stdin, stdout, stderr)
        _variable_expr_cache[name] = variable_expr
        return variable_expr

command_breaking_chars = '\r\n;|'
pipeline_breaking_chars = '\r\n;'

def parse_dollars_expr(string, pos=0):
    if pos >= len(string):
        raise SyntaxError("unexpected end of expression")
    char = string[pos]
    if char.isspace():
        raise SyntaxError("unexpected whitespace")
    elif char == '$':
        return pos+1, '$'
    else:
        expr = [char]
        pos += 1
        while pos < len(string) and not string[pos].isspace() and string[pos] not in command_breaking_chars:
            expr.append(string[pos])
            pos += 1
        return pos, get_variable_expr(''.join(expr))

def match_glob(text, glob, wildcards, t=0, g=0):
    while g < len(glob):
        if g in wildcards:
            star_p = q_cnt = 0
            while g < len(glob):
                if glob[g] == '*':
                    star_p = True
                elif glob[g] == '?':
                    q_cnt += 1
                else:
                    break
                g += 1
            t += q_cnt
            if t > len(text):
                return False
            if star_p:
                if g == len(glob):
                    return True
                for i in xrange(t, len(text)):
                    if text[i] == glob[g] and match_glob(text, glob, wildcards, i+1, g+1):
                        return True
                return False
            else:
                if t == len(text) and g == len(glob):
                    return True
        if t == len(text) or g == len(glob) or text[t] != glob[g]:
            return False
        t += 1
        g += 1
    return t == len(text)

def create_wildcard_expr(string, wildcards):
    if _windows:
        if string[1:2] == ':' and string[2:3] in ('/', '\\'):
            # absolute path starting with a drive
            parent = string[0:3]
            pos = 3
        elif string[0] in ('/', '\\'):
            parent = string[0]
            pos = 1
        else:
            parent = ''
            pos = 0
        string = string.replace('\\', '/')
    else:
        if string[0] == '/':
            parent = '/'
            pos = 1
        else:
            parent = ''
            pos = 0
    components = []
    while pos < len(string):
        if string[pos] == '/':
            pos += 1
            continue
        end = string.find('/', pos)
        if end == -1:
            end = len(string)
        components.append((string[pos:end], [x-pos for x in wildcards if pos <= x < end]))
        pos = end+1
    def wildcard_expr(shell, stdin, stdout, stderr):
        paths = [parent]
        for glob, wildcard in components:
            new_paths = []
            for path in paths:
                if wildcard:
                    try:
                        for subpath in os.listdir(os.path.join(shell.curdir, path)):
                            if match_glob(subpath, glob, wildcard):
                                new_paths.append(os.path.join(path, subpath))
                    except OSError:
                        pass
                else:
                    newpath = os.path.join(path, glob)
                    try:
                        if os.path.exists(os.path.join(shell.curdir, newpath)):
                            new_paths.append(newpath)
                    except OSError:
                        pass
            paths = new_paths
            if not paths:
                break
        if paths:
            return paths
        else:
            return [string]
    return wildcard_expr

def parse_command(string, pos=0):
    arglists = []
    args = []
    arg = []
    got_space = False
    unescaped_wildcards = []
    while pos < len(string) and string[pos] not in command_breaking_chars:
        char = string[pos]
        if char.isspace():
            if arg:
                if unescaped_wildcards:
                    if got_space and (args or arglists):
                        args.append('')
                    if args:
                        arglists.append(args)
                        args = []
                    arglists.append(create_wildcard_expr(''.join(arg), unescaped_wildcards))
                else:
                    if got_space and arglists and not args:
                        args.append('')
                    args.append(''.join(arg))
                arg = []
                unescaped_wildcards = []
            got_space = True
            pos += 1
        elif char == '$':
            pos, expr = parse_dollars_expr(string, pos+1)
            if isinstance(expr, basestring):
                arg.append(expr)
            else:
                if arg:
                    args.append(''.join(arg))
                    arg = []
                elif got_space:
                    args.append('')
                if args:
                    arglists.append(args)
                    args = []
                arglists.append(expr)
                got_space = False
        elif char in '*?':
            unescaped_wildcards.append(len(arg))
            arg.append(char)
            pos += 1
        else:
            arg.append(char)
            pos += 1
    if arg:
        if unescaped_wildcards:
            if got_space and (args or arglists):
                args.append('')
            if args:
                arglists.append(args)
                args = []
            arglists.append(create_wildcard_expr(''.join(arg), unescaped_wildcards))
        else:
            if got_space and arglists and not args:
                args.append('')
            args.append(''.join(arg))
    if args:
        arglists.append(args)
    return pos, CommandBlock([x for x in arglists if x != ['']], False)

def parse_pipeline(string, pos=0):
    commands = []
    while pos < len(string):
        pos, command = parse_command(string, pos)
        commands.append(command)
        if pos < len(string) and string[pos] == '|':
            pos += 1
            continue
        else:
            break
    if not commands:
        return pos, EmptyBlock()
    elif len(commands) == 1:
        return pos, commands[0]
    else:
        return pos, PipelineBlock(commands)

def parse_commands(string, pos=0):
    commands = []
    while pos < len(string):
        pos, command = parse_pipeline(string, pos)
        commands.append(command)
        if pos < len(string) and string[pos] == ';':
            pos += 1
            continue
        else:
            break
    if not commands:
        return pos, EmptyBlock()
    elif len(commands) == 1:
        return pos, commands[0]
    else:
        return pos, CommandSequenceBlock(commands)

class Shell(object):
    def __init__(self, curdir=None, environ=None):
        if curdir is None:
            curdir = os.getcwd()
        if environ is None:
            environ = EnvironDictionary(os.environ)
        self.curdir = curdir
        self.environ = environ

    def chdir(self, dirname):
        self.curdir = dirname

    def read_input(self):
        return None

    def run(self):
        cmd = self.read_input()
        while cmd is not None:
            code = parse_commands(cmd)[1]
            block = code.create_instance(self, self.stdin, self.stdout, self.stderr, ())
            block.run()
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

    def chdir(self, dirname):
        os.chdir(dirname)
        Shell.chdir(self, dirname)

    def __init__(self, *args, **kwargs):
        Shell.__init__(self, *args, **kwargs)
        self.stdin = sys.stdin
        self.stdout = sys.stdout
        self.stderr = sys.stderr

def main():
    curdir = os.getcwd()
    environ = EnvironDictionary(os.environ)
    shell = InteractiveShell(curdir, environ)
    shell.run()
    print ''

if __name__ == '__main__':
    main()

