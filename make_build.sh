#!/bin/bash

echo -e "\nBuild will be: "
git describe --tags --dirty --always

echo -e "\nWould you like to continue? (y/n)\n"
read -s -n 1 key

case $key in
    y|Y)
        mkdir -p build
        result=$(conda build conda.recipe --croot=build)
        if [ $? -ne 0 ]; then
            exit 1
        fi
        conda index ../build

        cd docs
        make html
        git add _build
        git commit -m "updating docs"
        ;;
    *)
        exit 0
        ;;
esac