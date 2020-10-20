from setuptools import setup, find_packages

with open('README.md') as readme_file:
    README = readme_file.read()

setup_args = dict(
    name='elektra',
    version='0.0.1',
    description='Power block price creation and conversion',
    long_description_content_type="text/markdown",
    long_description=README,
    license='MIT',
    packages=find_packages(),
    author='Molecule',
    author_email='devs@molecule.io',
    keywords=['Power', 'Prices'],
    url='https://github.com/wearemolecule/elektra',
    download_url='https://pypi.org/project/elektra/'
)

install_requires = [
    'python-dotenv',
    'pandas',
    'numpy'
]

if __name__ == '__main__':
    setup(**setup_args, install_requires=install_requires)
