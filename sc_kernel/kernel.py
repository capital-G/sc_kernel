import json
import platform
import sys
from functools import partial
import time
from subprocess import check_output
import re
from typing import Dict, Optional, List
import os

import pexpect
from IPython.lib.display import Audio
from IPython.display import Image
from metakernel import ProcessMetaKernel, REPLWrapper

from . import __version__

# idea from
# https://github.com/supercollider/qpm/blob/d3f72894e289744f01f3c098ab0a474d5190315e/qpm/sclang_process.py#L62

EXEC_WRAPPER = partial(
    """
var cwd = "{cwd}";
var plot = {{|w, fileName|
	var image;
	var filePath;
	1.0.wait;
	fileName = fileName ? "sc_%.png".format({{rrand(0, 9)}}.dup(10).join(""));
	filePath = cwd +/+ fileName;
	if(w.isKindOf(Plotter), {{
		w = w.parent;
	}});
	if(w.isNil, {{"Can not create image of closed window".throw;}});
	image = Image.fromWindow(w).write(filePath);
	"-----PLOTTED_IMAGE_%-----".format(filePath).postln;
	image;
}};

{{
    var result;
    "**** JUPYTER ****".postln;
    result = {{ try {{{code}}} {{|error| "ERROR %".format(error).postln}} }}.value();
    postf("-> %%\n", result);
    "**** /JUPYTER ****".postln;
}}.fork(AppClock);
""".format,  # noqa
    cwd=os.getcwd(),
)

SEARCH_CLASSES = partial(
    """
var getClasses = {{|t|
	var res = [];
	if(t.size>2, {{
		Class.allClasses.do({{ |class|
			var name = class.name.asString;
			if (name.beginsWith(t)) {{
				res = res.add(name);
			}};
		}});
	}});
	res.cs;
}};
getClasses.("{search_term}");
""".format  # noqa
)


class BgColors:
    # from https://stackoverflow.com/a/287944/3475778
    FAIL = "\033[91m"
    END = "\x1b[0m"


def get_kernel_json():
    """Get the kernel json for the kernel."""
    here = os.path.dirname(__file__)
    with open(os.path.join(here, "kernel.json")) as fid:
        data = json.load(fid)
    data["argv"][0] = sys.executable
    return data


class SCKernel(ProcessMetaKernel):
    app_name = "supercollider_kernel"
    name = "SuperCollider Kernel"
    implementation = "sc_kernel"
    implementation_version = __version__
    language = "supercollider"
    language_info = {
        "mimetype": "text/x-sclang",
        "name": "smalltalk",  # although supercollider is included in pygments its not working here
        "file_extension": ".scd",
        "pygments_lexer": "supercollider",
    }
    kernel_json = get_kernel_json()

    METHOD_DUMP_REGEX = re.compile(r"(\w*)\s*\(")
    HTML_HELP_FILE_PATH_REGEX = re.compile(r"-> file:\/\/(.*\.html)")
    SCHELP_HELP_FILE_PATH_REGEX = re.compile(r"<a href='file:\/\/(.*\.schelp)'>")
    SC_VERSION_REGEX = re.compile(r"sclang (\d+(\.\d+)+)")
    METHOD_EXTRACTOR_REGEX = re.compile(r"([A-Z]\w*)\.(.*)")
    RECORD_MAGIC_REGEX = re.compile(r"%%\s?record \"?([\w \.]*)\"?")
    PLOT_REGEX = re.compile(r"-{5}PLOTTED_IMAGE_(?P<ImagePath>.*)-{5}")

    @property
    def language_version(self):
        return self.SC_VERSION_REGEX.search(self.banner).group(1)

    @property
    def banner(self):
        return check_output([self._sclang_path, "-v"]).decode("utf-8")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sclang_path = self._get_sclang_path()
        self.__sclang: Optional[REPLWrapper] = None
        self.wrapper = self._sclang
        self.recording_paths = set()

    @staticmethod
    def _get_sclang_path() -> str:
        sclang_path = os.environ.get("SCLANG_PATH")
        if not sclang_path:
            p = platform.system()
            if p == "Linux":
                sclang_path = "sclang"
            if p == "Darwin":
                sclang_path = "/Applications/SuperCollider.app/Contents/MacOS/sclang"
            if p == "Windows":
                raise NotImplementedError
        return sclang_path  # type: ignore

    @property
    def _sclang(self) -> "ScREPLWrapper":
        if self.__sclang:
            return self.__sclang  # type: ignore
        self.__sclang = ScREPLWrapper(f"{self._sclang_path} -i jupyter")
        return self.__sclang

    def do_execute_direct(self, code: str, silent=False):
        if code == ".":
            code = "CmdPeriod.run;"
        for file_recording in self.RECORD_MAGIC_REGEX.findall(code):
            # check https://en.wikipedia.org/wiki/HTML5_audio#Supported_audio_coding_formats
            # for available formats in a browser and
            # http://doc.sccode.org/Classes/SoundFile.html#-headerFormat
            # for available SC formats
            _, file_ext = os.path.splitext(file_recording)
            if file_ext.lower() not in [".flac", ".wav"]:
                self.log.error("Only FLAC and WAV is supported for browser playback!")
            file_path = os.path.join(os.getcwd(), file_recording)
            self.log.info(f"Start recording to {file_path}")
            recording_code = f"""
            s.recorder.recHeaderFormat = "{file_ext[1:]}";
            s.recorder.recSampleFormat = "int24";
            s.record("{file_path}");
            """
            code = recording_code + code
            # remove magic from code execution
            code = self.RECORD_MAGIC_REGEX.sub("", code)

        return super().do_execute_direct(
            code=code,
            silent=silent,
        )

    def _check_for_recordings(self, message):
        """
        As Jupyter Notebook struggles with audio files that are still written to we can only display
        audio files once they are fully written.
        As SuperCollider is only displaying the file name at the end

        :param message:
        :return:
        """
        # we also want to check the output that has been echoed before the matching of the regex
        # because the SClang recorder works prepares async and we will not capture its output
        # without preparing the record otherwise, check the docs
        # https://doc.sccode.org/Classes/Recorder.html
        message = message + self._sclang.before_output
        recording_paths: List[str] = self._sclang.RECORD_MATCHER_REGEX.findall(message)
        self.recording_paths.update(recording_paths)
        for recording_path in recording_paths:
            self.log.info(f"Found new recording: {recording_path}")

        finished_recordings: List[str] = self._sclang.RECORDING_STOPPED_REGEX.findall(
            message
        )

        displayed_recordings: List[str] = []
        for finished_recording in finished_recordings:
            for recording_path in [
                f for f in self.recording_paths if finished_recording in f
            ]:
                self.log.info(f"Found finished recording: {recording_path}")
                time.sleep(1.0)  # wait for finished writing, just in case
                self.Display(Audio(filename=recording_path))
                displayed_recordings.append(recording_path)
        self.recording_paths.difference_update(displayed_recordings)

    def _check_for_plot(self, message: str) -> str:
        image_path: str
        for image_path in self.PLOT_REGEX.findall(message):
            # in case the helper function gets printed
            if image_path == "%":
                continue
            self.Display(Image(filename=image_path))
        return self.PLOT_REGEX.sub("", message)

    def Write(self, message):
        self._check_for_recordings(message)
        message = self._check_for_plot(message)
        super().Write(message)

    @staticmethod
    def extract_class_name(obj: str) -> str:
        reverse_class_name = ""
        # not used but maybe later
        reverse_method_name = None  # noqa

        # chars which delimit a new class
        TERMINAL_CHARS = [" ", "(", ")"]

        for o in obj[::-1]:
            if o in TERMINAL_CHARS:
                break
            if o == ".":
                # everything after a . is a method - reset our counter
                reverse_method_name = reverse_class_name  # noqa
                reverse_class_name = ""
                continue
            reverse_class_name += o
        return reverse_class_name[::-1]

    def get_completions(self, info: Dict):
        class_name = self.extract_class_name(info["obj"])
        sc_string = self._sclang.run_command(
            SEARCH_CLASSES(search_term=class_name), timeout=5
        )
        # need to remove -> from interpreter
        return json.loads(sc_string[2:])

    def get_kernel_help_on(self, info: Dict, level=0, none_on_fail=False):
        code = self.extract_class_name(info["obj"])
        output = self._sclang.run_command(f'SCDoc.findHelpFile("{code}");')
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


class ScREPLWrapper(REPLWrapper):
    def __init__(self, cmd_or_spawn, *args, **kwargs):
        cmd = pexpect.spawn(cmd_or_spawn, encoding="utf-8")
        try:
            # we wait for the Welcome message and throw everything before it away as well
            cmd.expect("Welcome to SuperCollider.*", timeout=15)
        except pexpect.TIMEOUT as e:
            print(f"Could not start sclang successfully: {e}")
            raise e

        super().__init__(
            cmd,
            prompt_regex="",
            prompt_change_cmd="",
            new_prompt_regex="",
            prompt_emit_cmd="",
            *args,
            **kwargs,
        )
        self.child: pexpect.spawn
        # increase buffer size so streaming of large data goes much faster
        # https://pexpect.readthedocs.io/en/stable/api/pexpect.html#spawn-class
        self.child.maxread = 200000
        self.child.searchwindowsize = None

    BEGIN_TOKEN = "**** JUPYTER ****"
    END_TOKEN = "**** /JUPYTER ****"
    COMMAND_REGEX = re.compile(
        r"\*{4} JUPYTER \*{4}(?P<Content>.*)\*{4} /JUPYTER \*{4}", re.DOTALL
    )
    ERROR_REGEX = re.compile(
        r"(\*{4} JUPYTER \*{4})?(?P<Content>.*ERROR: .*\-{35})", re.DOTALL
    )
    THROW_REGEX = re.compile(r"(?P<Content>(ERROR: .*)?CALL STACK:)", re.DOTALL)
    RECORD_MATCHER_REGEX = re.compile(
        r"Recording channels \[[\d ,]*\] \.\.\. \npath: \'(.*)'", re.MULTILINE
    )
    RECORDING_STOPPED_REGEX = re.compile(r"Recording Stopped: \((.*)\)")

    def run_command(self, command, timeout=30, *args, **kwargs):
        """
        In order to know when a command was finished and is ready for another prompt
        we encapsulate every command with
        "**** JUPYTER ****".postln;
        command
        "**** /JUPYTER ****".postln;

        :param timeout: Time to wait for execution, otherwise an Exception will be raised
        :param command: command to perform
        :param args:
        :param kwargs:
        :return: output of command as a string
        """
        # 0x1b is the escape key which tells sclang to evaluate any command b/c
        # we can not use \n as we can have multiple lines in our command
        self.child.sendline(f"{EXEC_WRAPPER(code=command)}{chr(0x1b)}")

        self.child.expect(
            [self.COMMAND_REGEX, self.ERROR_REGEX, self.THROW_REGEX], timeout=timeout
        )

        # although \r\n is DOS style it is for some reason used by UNIX, see
        # https://pexpect.readthedocs.io/en/stable/overview.html#find-the-end-of-line-cr-lf-conventions
        # we also remove \r\n at start and end of each command with the slicing [2:-2]
        output = self._clean_output(
            self.child.match.groupdict().get("Content", "ERROR")
        )
        # output = self.child.match.groups()[0][2:-2].replace('\r\n', '\n')
        if "ERROR: " in output:
            output += self.child.readline().replace("\r\n", "\n")
            # add red color for fail
            output = f"{BgColors.FAIL} {output} {BgColors.END}"
        return output

    @staticmethod
    def _clean_output(output: str) -> str:
        """
        Cleans the output which is obscured by various \r\n

        :param output:
        :return:
        """
        if output.startswith("\r\n"):
            output = output[2:]
        if output.endswith("\r\n"):
            output = output[:-2]
        return output.replace("\r\n", "\n")

    @property
    def before_output(self) -> str:
        """
        Returns the output that has been yielded before the matching regex.
        This returns output that has been called async before, like ``s.boot;`` does.
        :return:
        """
        return self._clean_output(self.child.before)
