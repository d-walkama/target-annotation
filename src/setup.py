from setuptools import setup
import versioneer

with open("requirements.txt", "r", encoding="UTF-8") as f:
    requirements = f.read().splitlines()

setup(
    name="target-annotation",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description="This package will provide modules to annotate targets",
    author="Derek Walkama",
    author_email="derek.m.walkama@gmail.com",
    packages=["target_annotation", "target_annotation.utils"],
    install_requires=requirements,
    keywords="target-annotation",
)
