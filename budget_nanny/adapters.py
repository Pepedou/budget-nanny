import collections

from budget_nanny.budgets import default_budget_requester

import_counter = collections.Counter()
accounts = default_budget_requester.get_accounts()


def get_import_id_for_transaction(transaction):
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

    import_counter.update([key_for_counter])
    counts_for_this_transaction = import_counter[key_for_counter]

    return f'YNAB:{transaction_amount}:{transaction_date}:{counts_for_this_transaction}'


def bank_to_ynab(bank_transaction):
    ynab_transaction = {
        'account_id': get_ynab_account_id_for_bank_account(bank_transaction['account']),
        'date': bank_transaction['date'].date().isoformat(),
        'amount':
            int((bank_transaction['outflow'] * -1) * 1000)
            if bank_transaction['outflow']
            else int(bank_transaction['inflow'] * 1000),
        'payee_id': None,
        'payee_name': bank_transaction['payee'][:50],
        'category_id': None,
        'memo': 'Imported by Budget Nanny',
    }

    import_id = get_import_id_for_transaction(ynab_transaction)

    ynab_transaction.update({'import_id': import_id})

    return ynab_transaction


def get_ynab_account_id_for_bank_account(bank_account):
    global accounts
    matching_accounts = [x for x in accounts if x['name'] == bank_account]

    return matching_accounts[0]['id'] if matching_accounts else None


def bank_to_ynab_multi(bank_transactions):
    return map(bank_to_ynab, bank_transactions)
