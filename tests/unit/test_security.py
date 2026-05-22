from app.core.security import create_access_token, get_password_hash, verify_password


def test_password_hash_and_verify():
    password = "supersecret"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrong", hashed)


def test_create_access_token():
    token = create_access_token(subject=1)
    assert isinstance(token, str)
    assert len(token) > 0
