"""Tests voor de self-update API (Beheer -> Onderhoud). Git wordt gemockt zodat
er geen echte netwerk-/git-operatie nodig is. Client-fixture = beheerder."""
import types
import api_update


def _cp(stdout='', returncode=0, stderr=''):
    return types.SimpleNamespace(stdout=stdout, stderr=stderr, returncode=returncode)


def _fake_git_factory(behind):
    def fake_git(*args, timeout=30):
        a = list(args)
        if a[0] == 'fetch':
            return _cp()
        if a[:2] == ['rev-parse', 'HEAD']:
            return _cp('aaaaaaa1234\n')
        if a[:2] == ['rev-parse', 'origin/master']:
            return _cp('bbbbbbb5678\n')
        if a[0] == 'rev-list':
            return _cp(f'{behind}\n')
        if a[0] == 'log':
            return _cp('bbbbbbb fix iets\nccccccc nog iets\n')
        return _cp()
    return fake_git


def test_check_not_git_checkout(client, monkeypatch):
    monkeypatch.setattr(api_update, '_is_git_checkout', lambda: False)
    data = client.get('/api/update/check').get_json()
    assert data['git'] is False
    assert data['available'] is False


def test_check_update_available(client, monkeypatch):
    monkeypatch.setattr(api_update, '_is_git_checkout', lambda: True)
    monkeypatch.setattr(api_update, '_git', _fake_git_factory(2))
    data = client.get('/api/update/check').get_json()
    assert data['available'] is True
    assert data['behind'] == 2
    assert data['current'] == 'aaaaaaa'
    assert data['latest'] == 'bbbbbbb'
    assert len(data['commits']) == 2


def test_check_up_to_date(client, monkeypatch):
    monkeypatch.setattr(api_update, '_is_git_checkout', lambda: True)
    monkeypatch.setattr(api_update, '_git', _fake_git_factory(0))
    data = client.get('/api/update/check').get_json()
    assert data['available'] is False
    assert data['behind'] == 0
    assert data['commits'] == []


def test_apply_not_git_checkout(client, monkeypatch):
    monkeypatch.setattr(api_update, '_is_git_checkout', lambda: False)
    assert client.post('/api/update/apply', json={}).status_code == 400


def test_apply_runs_helper(client, monkeypatch):
    monkeypatch.setattr(api_update, '_is_git_checkout', lambda: True)
    called = {}

    def fake_run(cmd, capture_output=True, text=True, timeout=None):
        called['cmd'] = cmd
        return _cp('OK: aaa -> bbb (herstart volgt)')

    monkeypatch.setattr(api_update.subprocess, 'run', fake_run)
    rv = client.post('/api/update/apply', json={})
    assert rv.status_code == 200
    assert rv.get_json()['ok'] is True
    assert called['cmd'] == api_update.HELPER_CMD


def test_check_requires_beheerder(client):
    """Conciërge (geen beheerder) mag de update-API niet."""
    with client.session_transaction() as sess:
        sess['user'] = {'displayName': 'C', 'is_beheerder': False, 'allowed_vestiging_ids': [1]}
    assert client.get('/api/update/check').status_code == 403
    assert client.post('/api/update/apply', json={}).status_code == 403
