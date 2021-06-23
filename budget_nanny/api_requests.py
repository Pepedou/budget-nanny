import json
import os

import requests
import simplejson

from ynab.transactions import ynab_transactions_encoder

YNAB_API_KEY = os.environ.get('YNAB_API_KEY')
BUDGETS_ENDPOINT = 'https://api.youneedabudget.com/v1/budgets'

if not YNAB_API_KEY:
    raise ValueError(
        'Missing YNAB_API_KEY. Be sure to add a variable to your environment named YNAB_API_KEY specifying your '
        'personal access token to the YNAB API.\n'
        'You can get your API key here: https://app.youneedabudget.com/settings/developer.'
    )

ACCOUNTS_ENDPOINT = f'{BUDGETS_ENDPOINT}/budget_id/accounts'
CATEGORIES_ENDPOINT = f'{BUDGETS_ENDPOINT}/budget_id/categories'
PAYEES_ENDPOINT = f'{BUDGETS_ENDPOINT}/budget_id/payees'
TRANSACTIONS_ENDPOINT = f'{BUDGETS_ENDPOINT}/budget_id/transactions'

BUDGET_ENDPOINTS = {
    'accounts': ACCOUNTS_ENDPOINT,
    'categories': CATEGORIES_ENDPOINT,
    'payees': PAYEES_ENDPOINT,
    'transactions': TRANSACTIONS_ENDPOINT,
}


class APIRequester:
    headers = {'Authorization': f'Bearer {YNAB_API_KEY}'}

    def __init__(self):
        self.raw_response = None

    def get(self, endpoint):
        self.raw_response = requests.get(endpoint, headers=self.headers)

        response_wrapper = self._validate_response()

        return response_wrapper['data']

    def post(self, endpoint, data):
        self.raw_response = requests.post(
            endpoint,
            headers=self.headers,
            json=data
        )
        print(self.raw_response.request.body)
        response_wrapper = self._validate_response()
        return response_wrapper['data']

    def _validate_response(self):
        if not self.raw_response.ok:
            raise RuntimeError(f"Couldn't connect to API ({self.raw_response.status_code}): {self.raw_response.text}.")

        response_wrapper = json.loads(self.raw_response.text)

        if 'error' in response_wrapper:
            error = response_wrapper['error']
            raise RuntimeError(f"There was an error with the request: {error['name']} - {error['detail']})")

        return response_wrapper
