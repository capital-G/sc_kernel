# Supercollider Jupyter Kernel

This kernel allows running SuperCollider Code in a [Jupyter](https://jupyter.org/) environment.

![Demo Notebook](demo.jpg)

This implementation is more a POC and can not be considered alpha status.

## Usage

* Currently the `Cmd + .` command is not binded. Instead create a new cell with the content `.` and execute this cell. This will transform the command to `CommandPeriod.run;` which is what is actually called on the `Cmd + .` press in the IDE.

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
  we need to have access to `sc_kernel` which is yet not installed
  as a Python package.
