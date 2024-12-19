import pytest

@pytest.fixture(params=["red", "blue"], scope="session")
def color(request):
    return request.param

@pytest.fixture(params=["big", "small"], scope="session")
def size(request):
    return request.param

def test_dummy(color, size):
    ...
