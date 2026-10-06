from security import SessionStore, RateLimiter, add_user, read_users, verify_user


def test_passwords_are_salted_and_verified(tmp_path):
    path = tmp_path / "users.json"
    add_user("alice", "unique-example-password", path)
    add_user("bob", "unique-example-password", path)
    data = read_users(path)
    assert data["alice"]["hash"] != data["bob"]["hash"]
    assert "unique-example-password" not in path.read_text()
    assert verify_user("alice", "unique-example-password", path) == data["alice"]["id"]
    assert verify_user("alice", "wrong-password", path) is None
    assert verify_user("unknown", "wrong-password", path) is None


def test_session_expiry_and_revoke_remove_history():
    now = [0]
    store = SessionStore(clock=lambda: now[0])
    token = store.create("alice")
    session = store.get(token)
    session.messages.append({"text": "private"})
    assert token not in store.sessions
    now[0] = 901
    assert store.get(token) is None and session.messages == [] and session.revoked
    now[0] = 1000
    token = store.create("bob")
    session = store.get(token)
    now[0] = 1800
    assert store.get(token)
    now[0] = 2600
    assert store.get(token)
    now[0] = 2801
    assert store.get(token) is None  # absolute TTL even with activity
    token = store.create("alice")
    session = store.get(token)
    store.revoke(token)
    assert store.get(token) is None and session.revoked


def test_rate_limits_reset_after_window():
    now = [0]
    limit = RateLimiter(clock=lambda: now[0])
    assert limit.allow("login", 2, 60)
    assert limit.allow("login", 2, 60)
    assert not limit.allow("login", 2, 60)
    now[0] = 61
    assert limit.allow("login", 2, 60)
