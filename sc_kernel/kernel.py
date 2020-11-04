import signal
from subprocess import check_output
import re
from typing import Tuple

from ipykernel.kernelbase import Kernel
from pexpect import replwrap, EOF

__version__ = '0.0.1'

version_regex = re.compile(r'sclang (\d+(\.\d+)+)')


class SCLangKernel(Kernel):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # @todo make path proper
        self.sclang_path = '/Applications/SuperCollider.app/Contents/MacOS/sclang'
        self._start_sclang()

    implementation = 'sclang_kernel'
    implementation_version = __version__

    @property
    def language_version(self):
        return version_regex.search(self.banner).group(1)

    @property
    def banner(self):
        return check_output([self.sclang_path, '-v']).decode('utf-8')

    language_info = {
        'mimetype': 'text/supercollider',
        'name': 'SuperCollider',
        'file_extension': '.sc',
        'pygments_lexer': 'sc',  # fix
    }

    def _start_sclang(self):
        sig = signal.signal(signal.SIGINT, signal.SIG_DFL)
        try:
            self.sc_wrapper = replwrap.REPLWrapper(self.sclang_path, u'sc3>', None)
        finally:
            signal.signal(signal.SIGINT, sig)

    def _execute_sclang(self, code: str) -> Tuple[bool, str]:
        interrupted = False
        try:
            output = self.sc_wrapper.run_command(code.rstrip().replace('\n', ' '), timeout=None)
        except KeyboardInterrupt:
            self.sc_wrapper.child.sendintr()
            interrupted = True
            self.sc_wrapper._expect_prompt()
            output = self.sc_wrapper.child.before()
        except EOF as e:
            output = self.sc_wrapper.child.before + 'restarting sclang'
            self._start_sclang()

        return interrupted, output

    def do_execute(self, code, silent, store_history=True,
                   user_expressions=None, allow_stdin=False):
        interrupted, output = self._execute_sclang(code)

        if not silent:
            stream_content = {'name': 'stdout', 'text': output}
            self.send_response(self.iopub_socket, 'stream', stream_content)

        if interrupted:
            return {
                'status': 'abort',
                'execution_count': self.execution_count,
            }

        if 'ERROR' in output:
            return {
                'status': 'error',
                'execution_count': self.execution_count,
                'ename': '',
                'evalue': output,
                'traceback': []
            }

        return {
            'status': 'ok',
            'execution_count': self.execution_count,
            'payload': [],
            'user_expressions': {},
        }


if __name__ == '__main__':
    from ipykernel.kernelapp import IPKernelApp

    IPKernelApp.launch_instance(kernel_class=SCLangKernel)
