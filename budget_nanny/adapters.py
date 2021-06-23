import collections
import logging
from typing import List

from bank.transactions import BankTransaction
from budget_nanny.budgets import default_budget_requester
from payee import PayeeDataProvider
from ynab.transactions import YnabTransaction

_logger = logging.getLogger(__name__)

_import_counter = collections.Counter()
_accounts = default_budget_requester.get_accounts()


def get_ynab_account_id_for_bank_account(bank_account):
    matching_accounts = [x for x in _accounts if x['name'] == bank_account]

    return matching_accounts[0]['id'] if matching_accounts else None


def convert_bank_transactions_to_ynab_transactions(
        bank_transactions: List[BankTransaction],
        payee_data_provider: PayeeDataProvider
) -> List[YnabTransaction]:
    ynab_transactions = []

    for bank_transaction in bank_transactions:
        ynab_transactions.append(convert_bank_transaction_to_ynab_transaction(bank_transaction, payee_data_provider))

    return ynab_transactions


def convert_bank_transaction_to_ynab_transaction(
        bank_transaction: BankTransaction,
        payee_data_provider: PayeeDataProvider
) -> YnabTransaction:
    matched_payee = payee_data_provider.get_fuzzy_match_on_ynab_payees_with_bank_payee(bank_transaction)

    ynab_transaction = {
        'account_id': get_ynab_account_id_for_bank_account(bank_transaction.account),
        'date': bank_transaction.date.date().isoformat(),
        'amount': bank_transaction.amount,
        'payee_id': matched_payee.id,
        'payee_name': matched_payee.name,
        'memo': 'Imported by Budget Nanny',
        'category_id': None,
    }

    ynab_transaction.update({'import_id': _get_import_id_for_transaction(ynab_transaction)})

    return ynab_transaction


def _get_import_id_for_transaction(transaction: dict):
    """
    Transactions imported through File Based Import or Direct Import (not through the API) are assigned an import_id in
    the format: 'YNAB:[milliunit_amount]:[iso_date]:[occurrence]'. For example, a transaction dated 2015-12-30 in the
    amount of -$294.23 USD would have an import_id of 'YNAB:-294230:2015-12-30:1’. If a second transaction on the same
    account was imported and had the same date and same amount, its import_id would be 'YNAB:-294230:2015-12-30:2’.
    """
    account_id = transaction['account_id']
    transaction_date = transaction['date']
    transaction_amount = transaction['amount']

    key_for_counter = (
        account_id,
        transaction_date,
        transaction_amount,
    )

    _import_counter.update([key_for_counter])
    counts_for_this_transaction = _import_counter[key_for_counter]

    return f'YNAB:{transaction_amount}:{transaction_date}:{counts_for_this_transaction}'
