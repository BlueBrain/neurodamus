FROM ubuntu:22.04
MAINTAINER Weina Ji <weina.ji@epfl.ch>

# The default shell for the RUN instruction is ["/bin/sh", "-c"].
# Using SHELL instruction to change default shell for subsequent RUN instructions
SHELL ["/bin/bash", "-c"]

# Create a directory for installation
ARG WORKDIR=/opt/software
RUN mkdir $WORKDIR

# Install needed libs
RUN apt-get --yes -qq update \
 && apt-get --yes -qq upgrade \
 && apt-get --yes -qq install \
                      g++ \
                      gcc \
                      python3.10 \
                      python3-pip \
                      python3-venv \
                      git \
                      cmake \
                      libreadline-dev \
                      wget \
                      mpich libmpich-dev libhdf5-mpich-dev hdf5-tools

#build venv
RUN cd $WORKDIR \
 && python3 -m venv myenv \
 && source myenv/bin/activate \
#pip install libsonata
 && CC=mpicc CXX=mpic++ pip install git+https://github.com/BlueBrain/libsonata
ENV USR_VENV "$WORKDIR/myenv"

# Install libsonatareport
RUN cd $WORKDIR \
 && git clone https://github.com/BlueBrain/libsonatareport.git --recursive \
 && cd libsonatareport \
 && mkdir build && cd build \
 && cmake -DCMAKE_INSTALL_PREFIX=$(pwd)/install -DCMAKE_BUILD_TYPE=Release -DSONATA_REPORT_ENABLE_SUBMODULES=ON -DSONATA_REPORT_ENABLE_MPI=ON .. \
 && cmake --build . --parallel \
 && cmake --build . --target install
ENV SONATAREPORT_DIR "$WORKDIR/libsonatareport/build/install"

# Install neuron
RUN source $USR_VENV/bin/activate \ 
 && apt-get --yes -qq update \
 && apt-get --yes -qq install flex libfl-dev bison ninja-build \
 && pip install -U pip setuptools \
 && pip install -U "cython<3" pytest sympy jinja2 pyyaml numpy \
 && cd $WORKDIR \
 && git clone https://github.com/neuronsimulator/nrn.git \
 && cd nrn && mkdir build && cd build \
 && cmake -DPYTHON_EXECUTABLE=$(which python) -DCMAKE_INSTALL_PREFIX=$(pwd)/install -DNRN_ENABLE_MPI=ON -DNRN_ENABLE_INTERVIEWS=OFF \
 -DNRN_ENABLE_CORENEURON=ON -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++ -DCORENRN_ENABLE_REPORTING=ON -DCMAKE_PREFIX_PATH=$SONATAREPORT_DIR .. \
 && cmake --build . -- -j 2 \
 && cmake --build . --target install
ENV PATH "$WORKDIR/nrn/build/install/bin:$PATH"
ENV PYTHONPATH "$WORKDIR/nrn/build/install/lib/python:$PYTHONPATH"

#Build h5py with the local hdf5
RUN source $USR_VENV/bin/activate \
 && pip install -U pip setuptools \
 && pip install cython numpy wheel pkgconfig \
 && MPICC="mpicc -shared" pip install --no-cache-dir --no-binary=mpi4py mpi4py \
 && CC="mpicc" HDF5_MPI="ON" HDF5_INCLUDEDIR=/usr/include/hdf5/mpich HDF5_LIBDIR=/usr/lib/x86_64-linux-gnu/hdf5/mpich \
    pip install --no-cache-dir --no-binary=h5py h5py --no-build-isolation

# Install neurodamus and prepare HOC_LIBRARY_PATH
RUN source $USR_VENV/bin/activate \
 && cd $WORKDIR \
 && git clone https://github.com/BlueBrain/neurodamus.git \
 && cd neurodamus \
 && pip install . \
 && cp tests/share/hoc/* core/hoc/
ENV HOC_LIBRARY_PATH "$WORKDIR/neurodamus/core/hoc"
ENV NEURODAMUS_PYTHON "$WORKDIR/neurodamus/"
ENV EXTRA_MODS_DIR "$WORKDIR/neurodamus/core/mod"

ADD build_neurodamus.sh $WORKDIR/script/
ENV PATH "$WORKDIR/script:$PATH"

ENTRYPOINT ["bash"]
