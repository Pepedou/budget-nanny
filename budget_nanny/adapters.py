import collections
import logging
import re

from fuzzywuzzy import process
from iterfzf import iterfzf

from budget_nanny.budgets import default_budget_requester
from payee import Payee

_logger = logging.getLogger(__name__)

import_counter = collections.Counter()
accounts = default_budget_requester.get_accounts()
payees = default_budget_requester.get_payees()
payee_names = [x.name for x in payees]


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


def get_fuzzy_match_on_ynab_payees_with_bank_payee(payee_name_from_bank_statement: str, cache):
    clean_payee_name_from_bank_statement = clean_payee_name(payee_name_from_bank_statement)

    if clean_payee_name_from_bank_statement in cache:
        correct_payee = cache.get(clean_payee_name_from_bank_statement)
    else:
        correct_payee = foo(clean_payee_name_from_bank_statement)

    if correct_payee is None:
        correct_payee = create_new_payee(payee_name_from_bank_statement)

    print(f'"{clean_payee_name_from_bank_statement}" ==> "{correct_payee}"')

    cache.update({clean_payee_name_from_bank_statement: correct_payee})

    return correct_payee


def create_new_payee(name: str) -> Payee:
    payee_name = ''

    print(f'Payee "{name}" not found. Creating new one:')

    while not payee_name:
        selected = iterfzf(payee_names, multi=False, prompt=f"Is \"{name}\" any of these? > ")
        if selected is not None:
            return get_payee_by_name(selected)

        payee_name = input(f"What's the correct payee for \"{name}\"? > ").strip()
    return Payee(name=payee_name)


def foo(clean_payee_name_from_bank_statement) -> Payee:
    correct_payee = None
    payee_with_most_similar_name = process.extractOne(
        clean_payee_name_from_bank_statement,
        payee_names,
        score_cutoff=69
    )

    if payee_with_most_similar_name:
        matched_payee_name, score = payee_with_most_similar_name

        if score >= 90:
            correct_payee = get_payee_by_name(matched_payee_name)
        else:
            payee_was_matched_correctly = input(
                f'Is "{clean_payee_name_from_bank_statement}" the same as "{matched_payee_name}" ({score})? [y/N]'
            ).lower() == 'y'

            if payee_was_matched_correctly:
                correct_payee = get_payee_by_name(matched_payee_name)
#            else:
#                alternative_candidates = {}
#                for x in process.extractBests(clean_payee_name_from_bank_statement, payee_names, score_cutoff=69):
#                    printable_name = f'{x[0]} ({x[1]})'
#                    alternative_candidates.update({printable_name: x})
#
#                selected_alternative = iterfzf(
#                    alternative_candidates,
#                    multi=False,
#                    prompt=f'Choose a payee  for "{clean_payee_name_from_bank_statement}" > '
#                )
#
#                if selected_alternative is not None:
#                    correct_payee = get_payee_by_name(alternative_candidates[selected_alternative])
#
    if correct_payee is None:
        correct_payee = create_new_payee(clean_payee_name_from_bank_statement)

    return correct_payee


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
    ynab_transaction = {
        'account_id': get_ynab_account_id_for_bank_account(bank_transaction['account']),
        'date': bank_transaction['date'].date().isoformat(),
        'amount':
            int((bank_transaction['outflow'] * -1) * 1000)
            if bank_transaction['outflow']
            else int(bank_transaction['inflow'] * 1000),
        'payee_id': matched_payee.id,
        'payee_name': matched_payee.name,
        'category_id': None,
        'memo': 'Imported by Budget Nanny',
    }

    import_id = get_import_id_for_transaction(ynab_transaction)

    ynab_transaction.update({'import_id': import_id})

    return ynab_transaction


def clean_payee_name(payee_name: str) -> str:
    name_without_special_chars = re.sub('[*:/;]', '', payee_name)
    name_without_rfc = re.sub('RFC[:]?', '', name_without_special_chars)
    name_without_account_numbers = re.sub('\d{3,}\w*', '', name_without_rfc)
    name_without_long_whitespaces = re.sub(' {2,}', ' ', name_without_account_numbers).strip()
    name = rename_known_edge_cases(name_without_long_whitespaces)
    return name


def rename_known_edge_cases(payee_name: str):
    new_name = None
    if payee_name.startswith('PASE '):
        new_name= 'I+D México (Tag)'
    #elif 'SPEI' in payee_name:
    #    return 'SPEI'
    elif 'UBER EATS' in payee_name:
        new_name= 'Uber Eats'
    elif 'BANCA INTERNET' in payee_name:
        new_name= 'BBVA'
    elif 'PAGO TARJETA DE CREDITO' in payee_name or 'PAGO TDC' in payee_name:
        new_name= 'BBVA Platino'

    if new_name:
        print(f'Renaming "{payee_name}" to "{new_name}"')
        return new_name
    else:
        return payee_name


def get_payee_by_name(payee_name: str) -> Payee:
    try:
        return [x for x in payees if x.name == payee_name][0]
    except IndexError:
        raise ValueError(f"There's no Payee named \"{payee_name}\"")
