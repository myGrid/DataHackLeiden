

def test_exception_is_raised:
    with assert_raises(HTTPError) as cm:
         call_your_method(p1, p2)
    ex = cm.exception # raised exception is available through exception property of context
    ok_(excep.code == 401, 'HTTPError should be Unauthorized!')
