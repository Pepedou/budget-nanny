from budget_nanny.nanny import BudgetNanny
from budget_nanny.utils import timeit


def main():
    with timeit('Budget Nanny'):
        nanny = BudgetNanny()
        nanny.sync_bank_to_ynab()
        nanny.validate_budget()


if __name__ == '__main__':
    main()
