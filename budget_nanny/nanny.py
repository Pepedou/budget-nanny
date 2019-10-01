from budget_nanny.adapters import bank_to_ynab_multi
from budget_nanny.bank import get_transactions_for_all_accounts

from budget_nanny.budgets import default_budget_requester


class BudgetNanny:
    @staticmethod
    def sync_bank_to_ynab():
        bank_transactions = get_transactions_for_all_accounts()
        transactions_in_ynab_format = bank_to_ynab_multi(bank_transactions)
        default_budget_requester.create_transactions(transactions_in_ynab_format)

    def validate_budget(self):
        pass
