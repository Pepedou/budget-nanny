import logging
import os
import re

import simplejson
from bullet import YesNo, Input
from fuzzywuzzy import process
from iterfzf import iterfzf
from simplejson import JSONDecodeError
from termcolor import cprint, colored

from budget_nanny.budgets import BudgetRequester

_logger = logging.getLogger('budget_nanny')


class Payee:
    def __init__(self, payee_id=None, name=None):
        self.id = payee_id
        self.name = name
        self.clean_name = _clean_payee_name(self.name)

    def __str__(self):
        return self.clean_name


def _payee_encoder(obj):
    if isinstance(obj, Payee):
        return obj.__dict__
    raise TypeError(repr(obj) + ' is not JSON Serializable')


def _clean_payee_name(payee_name: str) -> str:
    name_without_special_chars = re.sub('[*:/;]', '', payee_name)
    name_without_rfc = re.sub('RFC[:]?', '', name_without_special_chars)
    name_without_account_numbers = re.sub('\d{4,}\w*', '', name_without_rfc)
    name_without_long_whitespaces = re.sub(' {1,}', ' ', name_without_account_numbers).strip()
    name = _rename_known_edge_cases(name_without_long_whitespaces)
    return name


def _rename_known_edge_cases(payee_name: str):
    new_name = None
    if payee_name.startswith('PASE '):
        new_name = 'I+D México (Tag)'
    # elif 'SPEI' in payee_name:
    #    return 'SPEI'
    elif 'UBER EATS' in payee_name:
        new_name = 'Uber Eats'
    elif 'BANCA INTERNET' in payee_name:
        new_name = 'BBVA'
    elif 'PAGO TARJETA DE CREDITO' in payee_name or 'PAGO TDC' in payee_name:
        new_name = 'BBVA Platino'
    elif payee_name.startswith('PAYPAL '):
        new_name = payee_name[len('PAYPAL '):]

    if new_name:
        cprint(f'Renaming "{payee_name}" to "{new_name}"', 'magenta', attrs=['dark'])
        return new_name
    else:
        return payee_name


class PayeeDataProvider:
    @property
    def payee_names(self):
        return [x.name for x in self.payees]

    def __init__(self, payee_requester: BudgetRequester):
        self.payees = [Payee(x['id'], x['name']) for x in payee_requester.get_payees()]
        self.cache = None
        self.cache_file = os.path.expanduser('~/.cache/budget-nanny.json')

    def __enter__(self):
        self.cache = {}
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r') as f:
                try:
                    cache = simplejson.load(f)
                    for k, v in cache.items():
                        self.cache[k] = Payee(v['id'], v['name'])
                    _logger.info(f'Loaded payee cache from {self.cache_file}')
                except JSONDecodeError:
                    print('Empty cache')

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        with open(self.cache_file, 'w') as f:
            simplejson.dump(self.cache, f, default=_payee_encoder)

    def get_payee_by_name(self, payee_name: str) -> Payee:
        try:
            return [x for x in self.payees if x.name == payee_name][0]
        except IndexError:
            raise ValueError(f"There's no Payee named \"{payee_name}\"")

    def get_fuzzy_match_on_ynab_payees_with_bank_payee(self, bank_transaction: 'BankTransaction'):
        if bank_transaction.payee.clean_name in self.cache:
            correct_payee = self.cache.get(bank_transaction.payee.clean_name)
        else:
            correct_payee = self._detect_payee(bank_transaction)

        if correct_payee is None:
            correct_payee = self.create_new_payee(bank_transaction.payee.clean_name)

        cprint(f'"{bank_transaction.payee}" ==> "{correct_payee}"', 'white', 'on_blue')

        self.cache.update({bank_transaction.payee.clean_name: correct_payee})

        return correct_payee

    def _detect_payee(self, bank_transaction: 'BankTransaction') -> Payee:
        correct_payee = None
        clean_payee_name_from_bank_statement = bank_transaction.payee.clean_name
        payee_with_most_similar_name = process.extractOne(
            clean_payee_name_from_bank_statement,
            self.payee_names,
            score_cutoff=69
        )

        if payee_with_most_similar_name:
            matched_payee_name, score = payee_with_most_similar_name

            if score >= 90:
                correct_payee = self.get_payee_by_name(matched_payee_name)
            else:
                payee_was_matched_correctly = YesNo(
                    colored(
                        f'Is "{bank_transaction.payee_name_with_amount} the same as "{matched_payee_name}" ({score})?',
                        'cyan',
                        attrs=['underline'])
                ).launch()

                if payee_was_matched_correctly:
                    correct_payee = self.get_payee_by_name(matched_payee_name)

        if correct_payee is None:
            correct_payee = self.create_new_payee(bank_transaction)

        return correct_payee

    def create_new_payee(self, bank_transaction: 'BankTransaction') -> Payee:
        payee_name = ''

        cprint(f'Payee "{bank_transaction.payee}" not found. Creating new one:', 'yellow')

        while not payee_name:
            selected = iterfzf(self.payee_names, multi=False,
                               prompt=f"Is \"{bank_transaction.payee_name_with_amount}\" any of these? > ")
            if selected is not None:
                return self.get_payee_by_name(selected)

            payee_name = Input(
                colored(f"  What's the correct payee for \"{bank_transaction.payee_name_with_amount}\"? > ",
                        attrs=['bold']), strip=True) \
                .launch()
        return Payee(name=payee_name)
