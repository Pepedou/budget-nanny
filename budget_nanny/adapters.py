import logging
import re

from fuzzywuzzy import process

from budget_nanny.budgets import default_budget_requester
from budget_nanny.transactions import YNABTransaction

_logger = logging.getLogger(__name__)

accounts = default_budget_requester.get_accounts()
payees = default_budget_requester.get_payees()
payee_names = [x['name'] for x in payees]


def bank_to_ynab_multi(bank_transactions):
    return map(bank_to_ynab, bank_transactions)


def bank_to_ynab(bank_transaction):
    score = 0
    matched_payee = None

    result = get_fuzzy_match_on_ynab_payees_with_bank_payee(bank_transaction['payee'])

    if result is not None:
        matched_payee, score = result

    amount = int((bank_transaction['outflow'] * -1) * 1000) \
        if bank_transaction['outflow'] \
        else int(bank_transaction['inflow'] * 1000)
    payee_name = matched_payee['name'] if matched_payee else clean_payee_name(bank_transaction['payee'])
    payee_id = matched_payee['id'] if matched_payee else None

    ynab_transaction = YNABTransaction(
        account_id=get_ynab_account_id_for_bank_account(bank_transaction['account']),
        date=bank_transaction['date'].date().isoformat(),
        amount=amount,
        payee_id=payee_id,
        payee_name=payee_name,
        memo='Imported by Budget Nanny',
    )

    _logger.debug(ynab_transaction)

    return ynab_transaction, score


already_asked = {}


def get_fuzzy_match_on_ynab_payees_with_bank_payee(payee_name_from_bank_statement):
    clean_payee_name_from_bank_statement = clean_payee_name(payee_name_from_bank_statement)
    result = process.extractOne(clean_payee_name_from_bank_statement, payee_names, score_cutoff=70)

    if result is None:
        return None

    matched_payee_name, score = result

    if score >= 90:
        is_same = True
        _logger.debug(f'Matched "{clean_payee_name_from_bank_statement}" to "{matched_payee_name}" ({score}).')
    else:
        key = (clean_payee_name_from_bank_statement, matched_payee_name,)
        if key not in already_asked:
            is_same = input(
                f'Is "{clean_payee_name_from_bank_statement}" the same as "{matched_payee_name}" ({score})? [y/N]'
            ).lower() == 'y'
            already_asked.update({key: is_same})
        else:
            is_same = already_asked.get(key)
            _logger.debug(
                f'Reusing answer ({"Yes" if is_same else "No"}) for "{clean_payee_name_from_bank_statement}" matches '
                f'"{matched_payee_name}" ({score})'
            )

<<<<<<< Updated upstream
    return [x for x in payees if x['name'] == matched_payee_name][0] if is_same else None


def bank_to_ynab(bank_transaction):
    matched_payee = get_fuzzy_match_on_ynab_payees_with_bank_payee(bank_transaction['payee'])

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
=======
    matched_payee = [x for x in payees if x['name'] == matched_payee_name][0]
    if is_same:
        return matched_payee, score
    else:
        return None
>>>>>>> Stashed changes


def get_ynab_account_id_for_bank_account(bank_account):
    global accounts
    matching_accounts = [x for x in accounts if x['name'] == bank_account]

    return matching_accounts[0]['id'] if matching_accounts else None


def clean_payee_name(payee_name):
    name_without_special_chars = re.sub('[*:/;]', '', payee_name)
    name_without_rfc = re.sub('RFC[:]?', '', name_without_special_chars)
    name_without_account_numbers = re.sub('\d{3,}\w*', '', name_without_rfc)
    name_without_long_whitespaces = re.sub(' {2,}', '', name_without_account_numbers)
    return name_without_long_whitespaces
