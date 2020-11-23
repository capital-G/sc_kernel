import time
from unittest import TestCase

from sc_kernel.kernel import ScREPLWrapper, SCKernel


class ScREPLWrapperTestCase(TestCase):
    def setUp(self):
        self.sclang_path = f'{SCKernel._get_sclang_path()} -i jupyter'

    def test_hello_world(self):
        repl = ScREPLWrapper(self.sclang_path)
        output = repl.run_command('"Hello World".postln;')
        self.assertEqual(output, 'Hello World\n-> Hello World')

    def test_error(self):
        repl = ScREPLWrapper(self.sclang_path)
        output = repl.run_command('0/nil;')
        self.assertTrue('ERROR: ' in output)

    def test_capture_async_output(self):
        repl = ScREPLWrapper(self.sclang_path)
        output = repl.run_command('fork({0.1.wait; "foo".postln;});')
        self.assertEqual(output, '-> a Routine')
        time.sleep(0.15)
        repl.run_command('2;')
        self.assertEqual(repl.before_output, 'foo')
