import itertools

from budget_nanny.api_requests import APIRequester, BUDGETS_ENDPOINT, BUDGET_ENDPOINTS

DEFAULT_BUDGET = 'TEST'


class BudgetRequester:
    def __init__(self, budget):
        self.budget = budget
        self.api_requester = APIRequester()

    def create_transaction(self, transaction_data):
        return self.api_requester.post(
            BUDGET_ENDPOINTS['transactions'].replace('budget_id', self.budget['id']), {
                'transaction': transaction_data
            }
        )

    def create_transactions(self, transactions):
        return self.api_requester.post(
            BUDGET_ENDPOINTS['transactions'].replace('budget_id', self.budget['id']), {
                'transactions': list(transactions)
            }
        )

    def get_accounts(self):
        return self._get_budget_collection('accounts')

    def get_categories(self):
        return self._get_budget_collection('categories')

    def get_payees(self):
        return self._get_budget_collection('payees')

    def get_transactions(self):
        return self._get_budget_collection('transactions')

    def _get_budget_collection(self, collection_key):
        return self.api_requester.get(
            BUDGET_ENDPOINTS[collection_key].replace('budget_id', self.budget['id'])
        )[collection_key]


def get_budgets():
    return APIRequester().get(BUDGETS_ENDPOINT)['budgets']


budgets = get_budgets()

default_budget = [x for x in budgets if x['name'] == DEFAULT_BUDGET][0]

default_budget_requester = BudgetRequester(default_budget)
