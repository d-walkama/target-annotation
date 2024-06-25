#!/bin/bash

git add -u
cd docs
make html
git add _build
git commit -m "updating docs"
cd ..

echo "current version: $(git describe --tags --dirty --always)"
read -p "build version: " BUILD_VERSION

git tag $BUILD_VERSION

echo -e "\nBuild will be: "
git describe --tags --dirty --always

echo -e "\nWould you like to continue? (y/n)\n"
read -s -n 1 key

case $key in
    y|Y)
        result=$(python -m build)
        if [ $? -ne 0 ]; then
            exit 1
        fi
        ;;
    *)
        exit 0
        ;;
esac