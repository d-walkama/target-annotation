#!/bin/bash

git add -u
cd docs
make html
git add _build
read -p "commit message: " COMMIT_MSG
git commit -m "$COMMIT_MSG"
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
        python -m build
        ;;
    *)
        exit 0
        ;;
esac