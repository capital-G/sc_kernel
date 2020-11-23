# Supercollider Jupyter Kernel

This kernel allows running [SuperCollider](https://supercollider.github.io/) Code in a [Jupyter](https://jupyter.org/) environment.

![Demo Notebook](demo.jpg)

## Installation

* [Install JupyterLab](https://jupyter.org/install) and [SuperCollider](https://supercollider.github.io/).

* To install the kernel execute

  ```shell
  pip install git+https://github.com/capital-G/sc_kernel.git
  ```
  
  If you have not installed SuperCollider in the default location you have to set a environment variable
  called `SCLANG_PATH` which points to the sclang executable.

* Start a new Jupyter Lab instance by executing `jupyter lab` in a console.

* To uninstall the kernel execute

  ```shell
  jupyter kernelspec uninstall sc_kernel
  ```

## Usage

### Stop sound

Currently the `Cmd + .` command is not binded. Instead create a new cell with a single dot
  
```
.
```

and execute this cell. This will transform the command to `CommandPeriod.run;` which is what is actually called on the `Cmd + .` press in the IDE.

 
 ### Recording
 
`sc_kernel` provides an easy way to record audio to the local directory and store it in the notebook
so one can later share the notebook with the sound examples embedded.

Assuming one has started the server, simply execute

```supercollider
%% recording "my_file.flac"

{SinOsc.ar(SinOsc.ar(200)*200)*0.2!2}.play;
```

to start the recording.

To stop the recording, simply stop the Server recording via

```supercollider
s.stopRecording;
```

If one has chosen FLAC or WAV as file format, one will see a playback menu for the file within the notebook.

![Recording magic](recording.png)

If an relative path is provided as filename it will be put relative to the folder where `jupyter lab` was executed.
If an absolute path is given the output will be directed to the absolute path.

Keep in mind that **good browser support only exists for FLAC** and with WAV the seeking does not work.
The standard recording format of supercollider AIFF is not supported by browsers.

### Autocomplete

Simply push `Tab` to see available autocompletions.

### Documentation

To display the documentation of a Class, simply prepend a `?` to it and execute it, e.g.

```supercollider
?SinOsc
```

## Installation / Development

* Clone the repository into a directory

  ```shell
  git clone git@github.com:capital-G/sc_kernel.git
  cd sc_kernel
  ```

* If one wants to add the kernel to an existing Jupyter installation one can execute

  ```shell
  jupyter kernelspec install sc_kernel
  ```

  and run `jupyter lab` from within the cloned directory as
  we need to have access to `sc_kernel`.

## Maintainers

* [Dennis Scheiba](https://dennis-scheiba.com)
