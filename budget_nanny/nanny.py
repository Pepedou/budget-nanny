import os
import pickle

from budget_nanny.adapters import bank_to_ynab_multi
from budget_nanny.bank import get_transactions_for_all_accounts

from budget_nanny.budgets import default_budget_requester


class BudgetNanny:
    @staticmethod
    def sync_bank_to_ynab():
        bank_transactions = get_transactions_for_all_accounts()
        with open(os.path.expanduser('~/cache'), 'rb') as f:
            try:
                cache = pickle.load(f)
            except EOFError:
                cache = {}
        transactions_in_ynab_format = bank_to_ynab_multi(bank_transactions, cache)
        default_budget_requester.create_transactions(transactions_in_ynab_format)
        with open(os.path.expanduser('~/cache'), 'wb') as f:
            pickle.dump(cache, f)

    def validate_budget(self):
        pass
