import logging
import os
import re

import simplejson
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
        return self.name


def _payee_encoder(obj):
    if isinstance(obj, Payee):
        return obj.__dict__
    raise TypeError(repr(obj) + ' is not JSON Serializable')


def _clean_payee_name(payee_name: str) -> str:
    name_without_special_chars = re.sub('[*:/;]', '', payee_name)
    name_without_rfc = re.sub('RFC[:]?', '', name_without_special_chars)
    name_without_account_numbers = re.sub('\d{2,}\w*', '', name_without_rfc)
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

    if new_name:
        cprint(f'Renaming "{payee_name}" to "{new_name}"', 'blue', attrs=['dark'])
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

    def get_fuzzy_match_on_ynab_payees_with_bank_payee(self, payee: Payee):
        if payee.clean_name in self.cache:
            correct_payee = self.cache.get(payee.clean_name)
        else:
            correct_payee = self.foo(payee.clean_name)

        if correct_payee is None:
            correct_payee = self.create_new_payee(payee.clean_name)

        print(f'"{payee.clean_name}" ==> "{correct_payee}"')

        self.cache.update({payee.clean_name: correct_payee})

        return correct_payee

    def foo(self, clean_payee_name_from_bank_statement) -> Payee:
        correct_payee = None
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
                payee_was_matched_correctly = input(
                    colored(
                        f'Is "{clean_payee_name_from_bank_statement}" the same as "{matched_payee_name}" ({score})? [y/N]',
                        'cyan',
                        attrs=['underline'])
                ).lower() == 'y'

                if payee_was_matched_correctly:
                    correct_payee = self.get_payee_by_name(matched_payee_name)
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
            correct_payee = self.create_new_payee(clean_payee_name_from_bank_statement)

        return correct_payee

    def create_new_payee(self, name: str) -> Payee:
        payee_name = ''

        cprint(f'Payee "{name}" not found. Creating new one:', 'yellow')

        while not payee_name:
            selected = iterfzf(self.payee_names, multi=False, prompt=f"Is \"{name}\" any of these? > ")
            if selected is not None:
                return self.get_payee_by_name(selected)

            payee_name = input(colored(f"\tWhat's the correct payee for \"{name}\"? > ", attrs=['bold'])).strip()
        return Payee(name=payee_name)
