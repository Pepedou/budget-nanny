from dataclasses import dataclass


@dataclass
class Payee:
    id: str = None
    name: str = None

    def __str__(self):
        return self.name
