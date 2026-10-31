"""Unit checks for authentication helpers; no running PostgreSQL is required.

After installing requirements, run: python -m backend.test_http_api
Integration checks against PostgreSQL remain in backend.test_db.
"""
import unittest

from backend.http_api import _hash_password, _new_session, _session_user_id, _verify_password


class AuthenticationHelperTests(unittest.TestCase):
    def test_password_hash_verifies_only_correct_password(self):
        saved = _hash_password("correct horse battery staple")
        self.assertNotIn("correct horse battery staple", saved)
        self.assertTrue(_verify_password("correct horse battery staple", saved))
        self.assertFalse(_verify_password("incorrect password", saved))

    def test_session_round_trip_and_signature_validation(self):
        token = _new_session(142)
        self.assertEqual(_session_user_id(token), 142)
        encoded, signature = token.rsplit(".", 1)
        tampered = encoded + "." + ("0" if signature[0] != "0" else "1") + signature[1:]
        self.assertIsNone(_session_user_id(tampered))

    def test_malformed_or_missing_sessions_are_rejected(self):
        self.assertIsNone(_session_user_id(None))
        self.assertIsNone(_session_user_id("not-a-session"))
        self.assertIsNone(_session_user_id("Zm9v.YmFy"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
