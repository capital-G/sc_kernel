import glob
from setuptools import setup, find_packages
from setuptools.command.install import install

with open('sc_kernel/__init__.py', 'rb') as fid:
    for line in fid:
        line = line.decode('utf-8')  # type: ignore
        if line.startswith('__version__'):  # type: ignore
            version = line.strip().split()[-1][1:-1]
            break

DISTNAME = 'sc_kernel'

DATA_FILES = [
    ('share/jupyter/kernels/sc_kernel', [
        '%s/kernel.json' % DISTNAME
    ] + glob.glob('%s/images/*.png' % DISTNAME)
     )
]


class install_with_kernel_spec(install):
    def run(self):
        install.run(self)


if __name__ == "__main__":
    setup(name="sc_kernel",
          author="Dennis Scheiba",
          version=version,
          cmdclass={'install': install_with_kernel_spec},
          url="https://github.com/capital-G/sc_kernel",
          license="BSD",
          long_description=open("README.md").read(),
          long_description_content_type='text/markdown',
          classifiers=["Framework :: IPython",
                       "License :: OSI Approved :: BSD License",
                       "Programming Language :: Python :: 3.6",
                       "Programming Language :: Python :: 3.7",
                       "Programming Language :: Python :: 3.8",
                       "Topic :: System :: Shells"],
          packages=find_packages(include=["sc_kernel", "sc_kernel.*"]),
          include_package_data=True,
          data_files=DATA_FILES,
          install_requires=[
              "metakernel>=0.23.0",
              "ipython>=4.0",
              "pygments>=2.1",
              "jupyterlab>= 2.0"
          ],
          extras_require={
              'dev': [
                  'coverage==5.2.1',
                  'flake8==3.8.3',
                  'unittest-xml-reporting==3.0.4',
                  'mypy==0.770',
              ]
          },
          python_requires='>=3.6',
          )
