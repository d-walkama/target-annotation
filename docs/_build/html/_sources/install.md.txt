# Conda Install Instructions

Here are the instructions for installing the target-annotation package into a Conda environment for use in Jupyter.

## To Install

1. Let's first add the channels we need to conda config and set a strict priority:

```bash
conda config --add channels conda-forge
conda config --set channel_priority strict
```

2. Now we can make an environment for using target-annotation:

```bash
conda create -n target-annotation -c ./build target-annotation
```

3. Finally lets make a kernel for Jupyterhub:

```bash
conda activate target-annotation
python -m ipykernel install --user --name=target-annotation
```

## To Update

```bash
conda activate target-annotation
conda update target-annotation
```

## To Check For Updates

```bash
conda search target-annotation
```