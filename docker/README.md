# Neurodamus Docker Image

## Requirements
You must have:
* [Docker Desktop](https://www.docker.com/) installed and running.
* [Git](https://git-scm.com/)

## Docker image
You can either build your own docker image using the recipe in this repository or pull the prebuilt image from the Docker Hub.

### Option 1: Build your docker image
Before building your own docker image, make sure that your Docker Desktop is configured with at least 6 GB memory. (Settings->Resources->Memory)
```
cd docker/
# build the neurodamus with the latest version of libsonata, libsonatareport and neuron
docker build -t neurodamus .
# or specify the version of the dependencies
docker build -t neurodamus --build-arg LIBSONATA_TAG=v0.1.21 --build-arg LIBSONATAREPORT_TAG=1.2.1 --build-arg NEURON_TAG=9.0a .
```
### Option 2: Pull the prebuilt image from Docker Hub
```
docker pull bluebrain/neurodamus
```
You can verify your image with the command `docker image ls`, for example:
```
$ docker image ls
REPOSITORY                            TAG       IMAGE ID       CREATED        SIZE
bluebrain/neurodamus                  latest    4784d73155e7   11 hours ago   4.08GB
```
## Docker containier
With the docker image, you can start a neurodamus container with an interative Bash shell and meanwhile mount your local folder which contains your mod files and the circuit data.
```
docker run --rm -it -v <folder_mods_circuit>:/mnt/mydata bluebrain/neurodamus
```
In the Bash shell, first build your mods:
```
cd /mnt/mydata/
cp $NEURODAMUS_MODS_DIR/* <your_mod_dir>/
build_neurodamus.sh <your_mod_dir>/
```

If you have additional hoc files, add the location to `$HOC_LIBRARY_PATH`
```
export HOC_LIBRARY_PATH=/mnt/mydata/<your_hoc_dir>:$HOC_LIBRARY_PATH
```

Then you are ready to start the simulation.

To run with a single process
```
./x86_64/special -mpi -python $NEURODAMUS_PYTHON/init.py --configFile=<your_folder>/simulation_config.json
```
To run with multiple processes in parallel, e.g. 4 processes
```
mpirun -np 4 ./x86_64/special -mpi -python $NEURODAMUS_PYTHON/init.py --configFile=<your_folder>/simulation_config.json
```
