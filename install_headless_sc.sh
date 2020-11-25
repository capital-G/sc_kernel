#!/bin/sh

# following https://github.com/supercollider/supercollider/blob/develop/README_LINUX.md
# we also install libudev-dev although it is not mandatory but otherwise it won't build
apt-get update && apt-get install --yes build-essential cmake libjack-jackd2-dev libsndfile1-dev libfftw3-dev libxt-dev libavahi-client-dev libudev-dev

git clone --recurse-submodules https://github.com/SuperCollider/SuperCollider.git

cd SuperCollider && mkdir -p build && cd build

# disable QT and other verbosity
cmake -DBUILD_TESTING=OFF -DENABLE_TESTSUITE=OFF -DINSTALL_HELP=OFF -DNO_X11=OFF -DSC_ABLETON_LINK=OFF -DSC_ED=OFF -DSC_EL=no -DSC_IDE=OFF -DSC_USE_QTWEBENGINE=OFF -DSC_VIM=OFF -DSUPERNOVA=OFF -DSC_QT=OFF -DCMAKE_INSTALL_PREFIX=/usr/local ..

make

make install
