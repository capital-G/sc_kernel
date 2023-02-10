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
        self.assertTrue(str(self.sc_kernel.language_version).startswith("3"))

    def test_banner(self):
        self.assertTrue(self.sc_kernel.banner.startswith("sclang 3."))

    def _stream_writer(self, message):
        self.sc_output.write(message)
        self.sc_output.seek(0)

    def test_do_execute_direct(self):
        self.sc_kernel.do_execute_direct('"foo".postln;')
        self.assertEqual(self.sc_output.read(), "foo\n-> foo")

    def test_mute(self):
        self.sc_kernel.do_execute_direct(".")
        self.assertEqual(self.sc_output.read(), "-> CmdPeriod")

    def test_recorder_regex(self):
        some_text = """
        --> "Hello World"
        -----RECORDED_AUDIO_/home/sc.flac-----
        """
        parsed_text = self.sc_kernel._check_for_recordings(some_text)
        self.assertTrue("-----RECORDED_AUDIO" not in parsed_text)
        self.assertTrue("Error displaying /home/sc.flac" in parsed_text)

    def test_plot_regex(self):
        some_text = """
        --> "Hello World"
        -----PLOTTED_IMAGE_/home/sc.png-----
        """
        parsed_text = self.sc_kernel._check_for_plot(some_text)
        self.assertTrue("-----PLOTTED_IMAGE" not in parsed_text)
        self.assertTrue("Error displaying /home/sc.png" in parsed_text)

    def test_get_completions(self):
        # test class completion
        self.assertTrue("SinOscFB" in self.sc_kernel.get_completions({"obj": "SinO"}))

        # test too short
        self.assertTrue(len(self.sc_kernel.get_completions({"obj": "Si"})) == 0)
        # test method completion
        # c = self.sc_kernel.get_completions({'obj': 'SinOsc.a'})
        # self.assertTrue('SinOsc.asSymbol' in c)

    def test_get_kernel_help_on(self):
        h = self.sc_kernel.get_kernel_help_on({"obj": "SinOsc.ar"})
        self.assertTrue("Generates a sine wave" in h)
        h = self.sc_kernel.get_kernel_help_on({"obj": "Aasfasd"})
        self.assertTrue("Did not find any help" in h)

    def test_extract_class_name(self):
        test_cases = [
            ["SinOsc", "SinOsc"],
            ["S", "S"],
            ["SinOsc.kr", "SinOsc"],
            ["EnvGen(Env.adsr", "Env"],
        ]
        for test_case in test_cases:
            test_input, test_should = test_case
            self.assertEqual(self.sc_kernel.extract_class_name(test_input), test_should)


class ScREPLWrapperTestCase(TestCase):
    def setUp(self):
        # slow down?
        time.sleep(0.1)
        self.sclang_path = f"{SCKernel._get_sclang_path()} -i jupyter"

    def test_hello_world(self):
        try:
            repl = ScREPLWrapper(self.sclang_path)
            output = repl.run_command('"Hello World".postln;')
            self.assertEqual(output, "Hello World\n-> Hello World")
        finally:
            repl.terminate()

    def test_fail(self):
        try:
            repl = ScREPLWrapper(self.sclang_path)
            output = repl.run_command("foo+2;")
            # print red
            self.assertTrue("\033[91m" in output)
            self.assertTrue("Variable 'foo' not defined." in output)
            # stop printing in style
            self.assertTrue("\x1b[0m" in output)
        finally:
            repl.terminate

    def test_invalid_command(self):
        try:
            repl = ScREPLWrapper(self.sclang_path)
            output = repl.run_command("0/nil;")
            self.assertTrue("ERROR a BinaryOpFailureError" in output)
        finally:
            repl.terminate()

    def test_capture_async_output(self):
        try:
            repl = ScREPLWrapper(self.sclang_path)
            output = repl.run_command('fork({0.1.wait; "foo".postln;});')
            self.assertEqual(output, "-> a Routine")
            time.sleep(0.15)
            repl.run_command("2;")
            self.assertEqual(repl.before_output, "foo")
        finally:
            repl.terminate()

    def test_throw(self):
        try:
            repl = ScREPLWrapper(self.sclang_path)
            output = repl.run_command('"foo".throw;')
            self.assertEqual(output, "-> foo")
        finally:
            repl.terminate()

    def test_comment(self):
        try:
            repl = ScREPLWrapper(self.sclang_path)
            output = repl.run_command(
                """
            // foobar
            2+2;
            """
            )
            self.assertEqual(output, "-> 4")
        finally:
            repl.terminate()
