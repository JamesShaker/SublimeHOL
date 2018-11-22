import re
import os
import sublime
import signal
from sublime import load_settings, error_message
from .subprocess_repl import SubprocessRepl

class SublimeHOLRepl(SubprocessRepl):
    TYPE = "sublime_hol"

    def __init__(self, encoding, cmd=None, **kwds):
        super(SublimeHOLRepl, self).__init__(encoding, cmd=cmd, preexec_fn=os.setsid, **kwds)
   
    def write(self, command):
        #strip the command of terms and strings and comments
        stripped_command = re.sub('“([\w\s\S]*?)”','',command)
        stripped_command = re.sub('‘([\w\s\S]*?)’','',command)
        stripped_command = re.sub('\`([\w\s\S]*?)\`','',stripped_command)
        stripped_command = re.sub('\"([\w\s\S]*?)\"','',stripped_command)
        stripped_command = re.sub('\“([\w\s\S]*?)\”','',stripped_command)
        stripped_command = re.sub('\‘([\w\s\S]*?)\’','',stripped_command)
        stripped_command = re.sub('\(\*([\w\s\S]*?)\*\)','',stripped_command)

        #get open dependencies
        open_lines       = re.findall('open (.*?);',stripped_command)
        open_deps        = " ".join(open_lines).split(" ")

        #get dot dependecies
        dot_deps         = re.findall('(\w*?)\.(?:.*?)',stripped_command)

        #create dependencies loading string
        deps = list(set(open_deps + dot_deps))
        dep_string = ""
        for dep in deps:
            if dep != "" and dep != "HOL_Interactive":
                dep_string += 'load "' + dep + '";\n'

        #run final command
        new_cmd = dep_string + command
        return super(SublimeHOLRepl, self).write(new_cmd)
    def send_signal(self, sig):
        if sig == signal.SIGTERM:
            self._killed = True
        if self.is_alive():
            #Need to send signal to children because HOL runs everything
            #in build heap
            print("Trying to get group of " + str(self.popen.pid) + " killed with signal " + str(sig))
            os.killpg(os.getpgid(self.popen.pid), sig)