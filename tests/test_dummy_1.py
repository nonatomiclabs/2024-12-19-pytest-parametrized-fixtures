import pytest

@pytest.fixture(params=["red", "blue"])
def color(request):
    return request.param

def test_dummy(color):
    ...
