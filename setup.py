import setuptools

with open("README.md", "r") as fh:
    README = fh.read()

setuptools.setup(
    name="elektra",
    version="0.0.2",
    author="Molecule",
    author_email="devs@molecule.io",
    description="Power block price creation and conversion",
    long_description=README,
    long_description_content_type="text/markdown",
    url='https://github.com/wearemolecule/elektra',
    packages=setuptools.find_packages(),
    license='MIT',
    python_requires='>=3.8',
)