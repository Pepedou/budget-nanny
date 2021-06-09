import collections
import logging
import re

from fuzzywuzzy import process

from budget_nanny.budgets import default_budget_requester

_logger = logging.getLogger(__name__)

import_counter = collections.Counter()
accounts = default_budget_requester.get_accounts()
payees = default_budget_requester.get_payees()


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


def get_fuzzy_match_on_ynab_payees_with_bank_payee(payee_name_from_bank_statement, cache):
    payee_names = [x['name'] for x in payees]

    clean_payee_name_from_bank_statement = clean_payee_name(payee_name_from_bank_statement)
    result = process.extractOne(clean_payee_name_from_bank_statement, payee_names, score_cutoff=70)

    if not result:
        return None

    matched_payee_name, score = result

    if score >= 90:
        is_same = True
        _logger.info(f'Matched "{clean_payee_name_from_bank_statement}" to "{matched_payee_name}" ({score}).')
    else:
        key = (clean_payee_name_from_bank_statement, matched_payee_name,)
        if key not in cache:
            is_same = input(
                f'Is "{clean_payee_name_from_bank_statement}" the same as "{matched_payee_name}" ({score})? [y/N]'
            ).lower() == 'y'
            cache.update({key: is_same})
        else:
            is_same = cache.get(key)
            _logger.debug(
                f'Reusing answer ({"Yes" if is_same else "No"}) for "{clean_payee_name_from_bank_statement}" matches '
                f'"{matched_payee_name}" ({score})'
            )

    return [x for x in payees if x['name'] == matched_payee_name][0] if is_same else None


def get_ynab_account_id_for_bank_account(bank_account):
    global accounts
    matching_accounts = [x for x in accounts if x['name'] == bank_account]

    return matching_accounts[0]['id'] if matching_accounts else None


class Bob:
    def __init__(self):
        self.cache = None


bob = Bob()


def bank_to_ynab_multi(bank_transactions, pcache):
    bob.cache = pcache
    return map(bank_to_ynab, bank_transactions)


def bank_to_ynab(bank_transaction):
    matched_payee = get_fuzzy_match_on_ynab_payees_with_bank_payee(bank_transaction['payee'], bob.cache)

    payee_name = matched_payee['name'] if matched_payee else clean_payee_name(bank_transaction['payee'])
    ynab_transaction = {
        'account_id': get_ynab_account_id_for_bank_account(bank_transaction['account']),
        'date': bank_transaction['date'].date().isoformat(),
        'amount':
            int((bank_transaction['outflow'] * -1) * 1000)
            if bank_transaction['outflow']
            else int(bank_transaction['inflow'] * 1000),
        'payee_id': matched_payee['id'] if matched_payee else None,
        'payee_name': payee_name[:50],
        'category_id': None,
        'memo': 'Imported by Budget Nanny',
    }

    import_id = get_import_id_for_transaction(ynab_transaction)

    ynab_transaction.update({'import_id': import_id})

    return ynab_transaction


def clean_payee_name(payee_name):
    name_without_special_chars = re.sub('[*:/;]', '', payee_name)
    name_without_rfc = re.sub('RFC[:]?', '', name_without_special_chars)
    name_without_account_numbers = re.sub('\d{3,}\w*', '', name_without_rfc)
    name_without_long_whitespaces = re.sub(' {2,}', ' ', name_without_account_numbers)
    name = rename_known_edge_cases(name_without_long_whitespaces)
    return name


def rename_known_edge_cases(payee_name: str):
    if payee_name.startswith('PASE '):
        return 'I+D México (Tag)'
    elif 'SPEI' in payee_name:
        return 'SPEI'
    elif 'UBER EATS' in payee_name:
        return 'Uber Eats'
    elif 'BANCA INTERNET' in payee_name:
        return 'BBVA'
    elif 'PAGO TARJETA DE CREDITO' in payee_name or 'PAGO TDC' in payee_name:
        return 'BBVA Platino'

    return payee_name
