from app.evaluation.models import EvalTransaction

class BaselineStrategy:
    def name(self) -> str:
        raise NotImplementedError

    def evaluate(self, transaction: EvalTransaction) -> str:
        """Returns the selected intervention name."""
        raise NotImplementedError

class AlwaysRetryBaseline(BaselineStrategy):
    """
    A minimal baseline strategy that always recommends 'retry'.
    The policy gate will later decide if it's actually allowed based on the transaction.
    """
    def name(self) -> str:
        return "always_retry"

    def evaluate(self, transaction: EvalTransaction) -> str:
        return "retry"
