from ipykernel.kernelapp import IPKernelApp

from .kernel import SCKernel

IPKernelApp.launch_instance(kernel_class=SCKernel)
