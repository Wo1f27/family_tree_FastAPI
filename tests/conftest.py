# Регистрация фикстур для pytest
import pytest
from tests.fixtures.fixtures import *


# Убрать предупреждение про asyncio
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "asyncio: mark test as an asyncio test."
    )

