# Build Instructions

1. In order to build conda packages, you must install conda build:

    ```bash
    conda install conda-build
    ```

2. Then ensure you have a clean working tree (i.e. git status returns "nothing to commit, working tree clean") and that you have a git tag on HEAD with the current version of the package. For example:
   
    ```bash
    git status 
    git tag vX.X.X
    ```
The reason we want to do this is so that the versioneer package sets the package version equal to the git tag. If the working directory is not clean, the package version will be tagged as "dirty".

1. Modify requirements.txt to include any package requirements.

2. Run:

    ```bash
    ./make_build
    ```    
This will build the conda package within the repo, allowing versioneer to do its magic. It will then index the channel. Finally, it will rebuild the docs and commit/push the docs.
