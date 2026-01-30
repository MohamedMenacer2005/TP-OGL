
def test_will_pass():
    assert 1 + 1 == 2

def test_will_fail():
    assert 2 + 2 == 5  # This is wrong!

def test_another_fail():
    assert "hello".upper() == "GOODBYE"
