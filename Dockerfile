FROM python:3.10-bullseye

WORKDIR /home/sc_kernel

# compile/install supercollider w/o qt
RUN apt-get update && \
    apt-get install --yes \
        build-essential \
        cmake \
        libjack-jackd2-dev \
        libsndfile1-dev \
        libfftw3-dev \
        libxt-dev \
        libavahi-client-dev \
        libudev-dev && \
    git clone --recurse-submodules --depth=1 --branch 3.12 https://github.com/SuperCollider/SuperCollider.git && \
    cd SuperCollider && mkdir -p build && cd build && \
    cmake \
        -DBUILD_TESTING=OFF \
        -DENABLE_TESTSUITE=OFF \
        -DINSTALL_HELP=OFF \
        -DNO_X11=OFF \
        -DSC_ABLETON_LINK=OFF \
        -DSC_ED=OFF \
        -DSC_EL=no \
        -DSC_IDE=OFF \
        -DSC_USE_QTWEBENGINE=OFF \
        -DSC_VIM=OFF \
        -DSUPERNOVA=OFF \
        -DSC_QT=OFF \
        -DCMAKE_INSTALL_PREFIX=/usr/local \
        .. && \
    make && \
    make install && \
    cd .. && \
    rm -rf SuperCollider && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache \
    metakernel>=0.23.0 \
    ipython>=4.0 \
    pygments>=2.1 \
    jupyterlab>=2.0

ADD . .

RUN python setup.py install

EXPOSE 8888

ENTRYPOINT [ "jupyter", "lab", "--allow-root", "--ip=0.0.0.0", "--no-browser" ]