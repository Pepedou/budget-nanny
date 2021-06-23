from bullet import YesNo
from termcolor import colored, cprint

from adapters import convert_bank_transactions_to_ynab_transactions
from bank.transactions import get_transactions_for_all_accounts_from_spreadsheets
from budget_nanny.budgets import default_budget_requester
from payee import PayeeDataProvider


class BudgetNanny:
    @staticmethod
    def sync_bank_to_ynab():
        bank_transactions = get_transactions_for_all_accounts_from_spreadsheets()

        with PayeeDataProvider(default_budget_requester) as payee_data_provider:
            transactions_in_ynab_format = convert_bank_transactions_to_ynab_transactions(
                bank_transactions,
                payee_data_provider
            )
            should_post = YesNo(colored('Post to YNAB?', 'green', attrs=['bold', 'underline']), default='n').launch()

            if should_post:
                cprint('Posting to YNAB...', attrs=['dark'])
                default_budget_requester.create_multiple_transactions(transactions_in_ynab_format)
            else:
                cprint('Aborted!', 'grey', 'on_yellow')

    def validate_budget(self):
        pass
