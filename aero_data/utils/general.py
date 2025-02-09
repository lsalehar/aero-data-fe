import logging

logger = logging.getLogger(__name__)


def chunked(iterable, size):
    """Yield successive chunks from iterable of given size."""
    for i in range(0, len(iterable), size):
        yield iterable[i : i + size]
