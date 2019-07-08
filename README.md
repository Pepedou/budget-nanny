# Budget Nanny
![alt text](docs/nanny.png)

_Icon designed by Eucalyp from Flaticon._

A simple synchronization application and budget monitor for BBVA and YNAB written in Python3.

## Installation
You'll need at least python 3. This was tested with 3.7.

- Clone this repo.
  - `git clone https://github.com/Pepedou/budget-nanny`
- `cd` into the root directory.
  - `cd budget-nanny`
- Build the source code (using a virtual environment).
  - `python setup.py bdist_wheel`
- Install.
  - `pip install dist/budget_nanny-0.0.1-py3-none-any.whl`

## Run
- `YNAB_API_KEY=<your_key_here> nanny`
- Example: `YNAB_API_KEY=d432l4k2jl34kthisisfakejj23lk42l34k31283453 nanny`