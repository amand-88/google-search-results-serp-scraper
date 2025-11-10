from src.utils.pagination_helper import Pagination

def test_next_page_basic():
    next_page, next_start = Pagination.next_page(start=0, page_size=10, fetched=10)
    assert next_page == 2
    assert next_start == 10

def test_next_page_none_when_no_fetch():
    next_page, next_start = Pagination.next_page(start=20, page_size=10, fetched=0)
    assert next_page is None
    assert next_start is None