from typing import Optional, Tuple

class Pagination:
    @staticmethod
    def next_page(*, start: int, page_size: int, fetched: int) -> Tuple[Optional[int], Optional[int]]:
        """
        Given Google's current start index, the requested page size, and how many results were fetched,
        compute the next page number and next start index. If no next page is obvious, return (None, None).
        """
        if fetched <= 0:
            return None, None

        current_page = start // page_size + 1
        next_start = start + page_size
        next_page = current_page + 1
        return next_page, next_start