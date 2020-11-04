from ipykernel.kernelapp import IPKernelApp

from .kernel import SCLangKernel

IPKernelApp.launch_instance(kernel_class=SCLangKernel)
