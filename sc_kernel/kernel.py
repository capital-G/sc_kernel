import json
import platform
import sys
from subprocess import check_output
import re
from typing import Optional, List
import os

from metakernel import ProcessMetaKernel, REPLWrapper

__version__ = '0.2.0'


def get_kernel_json():
    """Get the kernel json for the kernel.
    """
    here = os.path.dirname(__file__)
    with open(os.path.join(here, 'kernel.json')) as fid:
        data = json.load(fid)
    data['argv'][0] = sys.executable
    return data


class SCKernel(ProcessMetaKernel):
    app_name = 'supercollider_kernel'
    name = 'SuperCollider Kernel'
    implementation = 'sc_kernel'
    implementation_version = __version__
    language = 'supercollider'
    language_info = {
        'mimetype': 'text/x-sclang',
        'name': 'smalltalk',  # although supercollider is included in pygments its not working here
        'file_extension': '.scd',
        'pygments_lexer': 'pygments.lexers.supercollider.SuperColliderLexer',
    }
    kernel_json = get_kernel_json()

    METHOD_DUMP_REGEX = re.compile(r'(\w*)\s*\(')
    HTML_HELP_FILE_PATH_REGEX = re.compile(r'-> file:\/\/(.*\.html)')
    SCHELP_HELP_FILE_PATH_REGEX = re.compile(r"<a href='file:\/\/(.*\.schelp)'>")
    SC_VERSION_REGEX = re.compile(r'sclang (\d+(\.\d+)+)')
    METHOD_EXTRACTOR_REGEX = re.compile(r'([A-Z]\w*)\.(.*)')

    @property
    def language_version(self):
        return self.SC_VERSION_REGEX.search(self.banner).group(1)

    @property
    def banner(self):
        return check_output([self._sclang_path, '-v']).decode('utf-8')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sclang_path = self._get_sclang_path()
        self.__sclang: Optional[REPLWrapper] = None
        self.__sc_classes: Optional[List[str]] = None
        self.wrapper = self._sclang

    @staticmethod
    def _get_sclang_path() -> str:
        sclang_path = os.environ.get('SCLANG_PATH')
        if not sclang_path:
            p = platform.system()
            if p == 'Linux':
                sclang_path = 'sclang'
            if p == 'Darwin':
                sclang_path = '/Applications/SuperCollider.app/Contents/MacOS/sclang'
            if p == 'Windows':
                pass
        return sclang_path

    @property
    def _sclang(self) -> REPLWrapper:
        if self.__sclang:
            return self.__sclang
        self.__sclang = REPLWrapper(
            self._sclang_path,
            prompt_regex='sc3> ',
            prompt_change_cmd=None,
        )
        return self.__sclang

    def do_execute_direct(self, code: str, silent=False):
        if code == '.':
            code = 'CmdPeriod.run;'
        super().do_execute_direct(
            code=code.rstrip().replace('\n', ' '),
            silent=silent,
        )

    @property
    def _sc_classes(self) -> List[str]:
        if self.__sc_classes:
            return self.__sc_classes
        self.__sc_classes = self._sclang.run_command("""
        Class.allClasses.do({|c|
             c.postln;
            nil;
        });
        """.replace('\n', ' ')).split('\n')[:-1]
        return self.__sc_classes

    def get_completions(self, info):
        code: str = info['obj']  # returns everything in the line before the cursor
        if '.' not in code:
            # only return classes if no dot is present
            return [c for c in self._sc_classes if c.startswith(code)]
        if code.count('.') == 1:
            # @todo too hacky :/
            sc_class, sc_method = self.METHOD_EXTRACTOR_REGEX.findall(code)[0]
            output = self._sclang.run_command(f'{sc_class}.dumpAllMethods;')
            return [f'{sc_class}.{m}' for m in self.METHOD_DUMP_REGEX.findall(output) if m.startswith(sc_method)]

    def get_kernel_help_on(self, info, level=0, none_on_fail=False):
        code = info['obj'].split('.')[0]
        output = self._sclang.run_command(f'{code}.helpFilePath')
        help_file_paths = self.HTML_HELP_FILE_PATH_REGEX.findall(output)
        if help_file_paths:
            if os.path.isfile(help_file_paths[0]):
                with open(help_file_paths[0].strip()) as f:
                    html = f.read()
                sc_help_file_paths = self.SCHELP_HELP_FILE_PATH_REGEX.findall(html)
                if sc_help_file_paths:
                    if os.path.isfile(sc_help_file_paths[0]):
                        with open(sc_help_file_paths[0]) as f:
                            return f.read()

        return f"Did not find any help for {code}"
