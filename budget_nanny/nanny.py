import logging
import readline

from budget_nanny.adapters import bank_to_ynab_multi, get_fuzzy_match_on_ynab_payees_with_bank_payee, payees
from budget_nanny.autocomplete import SimpleCompleter
from budget_nanny.bank import get_transactions_for_all_accounts
from budget_nanny.budgets import default_budget_requester
from budget_nanny.utils import timeit

_logger = logging.getLogger(__name__)


class BudgetNanny:
    @staticmethod
    def sync_bank_to_ynab():
        completer = SimpleCompleter([x['name'] for x in payees])
        # Register our completer function
        readline.set_completer(completer.complete)
        # Use the tab key for completion
        readline.parse_and_bind('tab: complete')

        bank_transactions = get_transactions_for_all_accounts()
        with timeit('test'):
            transactions_in_ynab_format = bank_to_ynab_multi(bank_transactions)
            filtered = [x for x in transactions_in_ynab_format if x[1] < 70]

        _logger.info(f'There are {len(filtered)} matches with low confidence.')

        while True:
            want_to_edit = input('Do you want to edit something? [y/N]').lower()
            if want_to_edit == 'y':
                want_to_edit = True
                break
            elif want_to_edit == 'n':
                want_to_edit = False
                break

        if want_to_edit:
            while True:
                # print(transactions_in_ynab_format)
                # which = [x.lower() for x in input('Which transactions? ').split()]
                # filtered = [x for x in transactions_in_ynab_format if x[0].import_id.lower() in which]

                if not filtered:
                    print('Transactions not found.')
                    break

                for transaction_to_edit, score in filtered:
                    confirm = input(f'Do you want to edit: {transaction_to_edit}? [y/N] ').lower() == 'y'

                    if not confirm:
                        continue

                    while True:
                        payee_name = input('New payee: ')

                        result = get_fuzzy_match_on_ynab_payees_with_bank_payee(payee_name)

                        if result is None:
                            print("Didn't find that payee.")
                            continue

                        matched_payee, score = result

                        transaction_to_edit.payee_id = matched_payee['id']
                        transaction_to_edit.payee_name = matched_payee['name']

                        print(f'Updated transaction: {transaction_to_edit}')
                        break

                if input('Quit? [y/N] ').lower() == 'y':
                    break

        default_budget_requester.create_transactions(
            {'transactions': [x.__dict__ for x, y in transactions_in_ynab_format]}
        )
