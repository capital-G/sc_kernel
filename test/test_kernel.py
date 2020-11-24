import time
from io import StringIO
from unittest import TestCase

from sc_kernel.kernel import ScREPLWrapper, SCKernel


class SCKernelTestCase(TestCase):
    def setUp(self):
        self.sc_kernel = SCKernel()
        self.sc_output = StringIO()
        self.sc_kernel.Write = self._stream_writer

    def tearDown(self):
        self.sc_kernel.do_shutdown(restart=False)

    def test_language_version(self):
        self.assertTrue(str(self.sc_kernel.language_version).startswith('3'))

    def test_banner(self):
        self.assertTrue(self.sc_kernel.banner.startswith('sclang 3.'))

    def _stream_writer(self, message):
        self.sc_output.write(message)
        self.sc_output.seek(0)

    def test_do_execute_direct(self):
        self.sc_kernel.do_execute_direct('"foo".postln;')
        self.assertEqual(self.sc_output.read(), 'foo\n-> foo')

    def test_mute(self):
        self.sc_kernel.do_execute_direct('.')
        self.assertEqual(self.sc_output.read(), '-> CmdPeriod')

    def test_recorder_magic(self):
        self.sc_kernel.do_execute_direct('%% record "foo.flac"')
        self.assertEqual(self.sc_output.read(), "server 'localhost' not running\n-> localhost")

    def test_sc_classes(self):
        self.assertTrue('Array' in self.sc_kernel._sc_classes)
        # test caching coverage
        self.assertTrue('Array' in self.sc_kernel._sc_classes)

    def test_get_completions(self):
        # test class completion
        self.assertTrue('Array' in self.sc_kernel.get_completions({'obj': "Arr"}))
        # test method completion
        c = self.sc_kernel.get_completions({'obj': 'SinOsc.a'})
        self.assertTrue('SinOsc.asSymbol' in c)

    def test_get_kernel_help_on(self):
        h = self.sc_kernel.get_kernel_help_on({'obj': 'SinOsc.ar'})
        self.assertTrue('Did not find any help' not in h)
        h = self.sc_kernel.get_kernel_help_on({'obj': 'Aasfasd'})
        self.assertTrue('Did not find any help' in h)


class ScREPLWrapperTestCase(TestCase):
    def setUp(self):
        self.sclang_path = f'{SCKernel._get_sclang_path()} -i jupyter'

    def test_hello_world(self):
        repl = ScREPLWrapper(self.sclang_path)
        output = repl.run_command('"Hello World".postln;')
        self.assertEqual(output, 'Hello World\n-> Hello World')
        repl.terminate()

    def test_error(self):
        repl = ScREPLWrapper(self.sclang_path)
        output = repl.run_command('0/nil;')
        self.assertTrue('ERROR: ' in output)
        repl.terminate()

    def test_capture_async_output(self):
        repl = ScREPLWrapper(self.sclang_path)
        output = repl.run_command('fork({0.1.wait; "foo".postln;});')
        self.assertEqual(output, '-> a Routine')
        time.sleep(0.15)
        repl.run_command('2;')
        self.assertEqual(repl.before_output, 'foo')
        repl.terminate()
