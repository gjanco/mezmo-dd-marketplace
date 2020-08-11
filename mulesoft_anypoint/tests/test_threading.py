import time

import pytest


def wait_func(ttw):
    time.sleep(ttw)


@pytest.mark.unit
def test_multithreading_pool(multithreading_pool_4):
    for i in range(16):
        ttw = 2
        if i >= 4:
            ttw = 3
        multithreading_pool_4.apply_async(wait_func, [ttw])
    time.sleep(1)
    for size in range(16, 0, -4):
        assert multithreading_pool_4.get_total_size() == size
        assert multithreading_pool_4.get_queue_size() == size - 4
        assert multithreading_pool_4.get_active_size() == 4
        if size == 16:
            time.sleep(2)
        else:
            time.sleep(3)
    multithreading_pool_4.wait_and_close()
    assert multithreading_pool_4.get_total_size() == 0


@pytest.mark.unit
def test_multithreading_pool_empty(multithreading_pool_4):
    for _ in range(4):
        ttw = 2
        multithreading_pool_4.apply_async(wait_func, [ttw])
    time.sleep(1)
    assert multithreading_pool_4.get_total_size() == 4
    assert multithreading_pool_4.get_queue_size() == 0
    assert multithreading_pool_4.get_active_size() == 4
    time.sleep(3)
    assert multithreading_pool_4.get_total_size() == 0
    assert multithreading_pool_4.get_queue_size() == 0
    assert multithreading_pool_4.get_active_size() == 0
    for _ in range(4):
        ttw = 2
        multithreading_pool_4.apply_async(wait_func, [ttw])
    time.sleep(1)
    assert multithreading_pool_4.get_total_size() == 4
    assert multithreading_pool_4.get_queue_size() == 0
    assert multithreading_pool_4.get_active_size() == 4
    multithreading_pool_4.wait_and_close()
    assert multithreading_pool_4.get_total_size() == 0
