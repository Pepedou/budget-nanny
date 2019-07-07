import setuptools

with open('./requirements.txt', 'r', encoding='utf-8') as reqs:
    requirements = reqs.read().splitlines()

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='budget-nanny',
    version='0.0.1',
    author='José Luis Valencia Herrera',
    description='A simple synchronization application and monitor for BBVA and YNAB',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/Pepedou/budget-nanny',
    packages=setuptools.find_packages(),
    install_requires=requirements,
    entry_points={
        'console_scripts': ['nanny=budget_nanny.run:main']
    },
)
