# https://www.blog.pythonlibrary.org/2021/09/23/python-101-how-to-create-a-python-package/
import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="elektra",
    version="0.0.29",
    author="Molecule",
    author_email="dev@molecule.io",
    description="Power block price creation and conversion",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/wearemolecule/elektra",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=setuptools.find_packages(),
    python_requires=">=3.7",
    install_requires=[
     "pandas",
     "numpy"
    ]
)
