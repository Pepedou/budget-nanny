import logging

from fuzzywuzzy import process


class SimpleCompleter:
    def __init__(self, options):
        self.matches = []
        self.options = sorted(options)

    def complete(self, text, state):
        if state == 0:
            # This is the first time for this text, so build a match list.
            if text:
                self.matches = [match for match, score in process.extractBests(text, self.options, score_cutoff=90, limit=10)]
                # print(self.matches)

                logging.debug('%s matches: %s', repr(text), self.matches)
            else:
                self.matches = self.options[:]
                logging.debug('(empty input) matches: %s', self.matches)

        # Return the state'th item from the match list,
        # if we have that many.
        try:
            response = self.matches[state] + " "
        except IndexError:
            response = None
        logging.debug('complete(%s, %s) => %s', repr(text), state, repr(response))

        return response
