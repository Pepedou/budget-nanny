import logging
import sys

from budget_nanny.nanny import BudgetNanny
from budget_nanny.utils import timeit

_logger = logging.getLogger('budget_nanny')


def main():
    setup_logging()
    with timeit('Budget Nanny'):
        nanny = BudgetNanny()
        nanny.sync_bank_to_ynab()


def setup_logging():
    """
    Sets up the loggers.
    """
    _logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')

    streaming_handler = logging.StreamHandler(sys.stdout)
    streaming_handler.setLevel(logging.DEBUG)
    streaming_handler.setFormatter(formatter)

    _logger.addHandler(streaming_handler)


if __name__ == '__main__':
    main()
