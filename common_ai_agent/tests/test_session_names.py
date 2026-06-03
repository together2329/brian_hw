import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.session_names import normalize_session_name


class TestSessionNameNormalization(unittest.TestCase):
    def test_accepts_user_ip_workflow_namespace(self):
        self.assertEqual(
            normalize_session_name("u-mabc123/dma330/rtl-gen"),
            "u-mabc123/dma330/rtl-gen",
        )

    def test_accepts_user_workspace_ip_workflow_namespace(self):
        self.assertEqual(
            normalize_session_name("alice/s1/NEWIP_MCTP/ssot-gen"),
            "alice/s1/NEWIP_MCTP/ssot-gen",
        )

    def test_accepts_four_level_session_path_with_marker(self):
        self.assertEqual(
            normalize_session_name(
                r"C:\repo\NEW_ATLAS\.session\alice\s1\NEWIP_MCTP\ssot-gen\conversation.json"
            ),
            "alice/s1/NEWIP_MCTP/ssot-gen",
        )

    def test_accepts_three_level_session_path_with_marker(self):
        self.assertEqual(
            normalize_session_name(
                r"C:\repo\NEW_ATLAS\.session\u-mabc123\dma330\ssot-gen\conversation.json"
            ),
            "u-mabc123/dma330/ssot-gen",
        )

    def test_accepts_session_marker_with_leading_slashes_and_extra_file(self):
        self.assertEqual(
            normalize_session_name(r"//.session\u-mabc123\dma330\ssot-gen\qa.json//"),
            "u-mabc123/dma330/ssot-gen",
        )

    def test_windows_scope_path_without_session_marker_keeps_ip_workflow_tail(self):
        self.assertEqual(
            normalize_session_name(r"C:\Users\207\Desktop\SQA\ssot-gen"),
            "SQA/ssot-gen",
        )

    def test_rejects_empty_session_marker_path(self):
        self.assertEqual(normalize_session_name(r"\.session\conversation.json"), "")

    def test_rejects_unsafe_session_segment(self):
        self.assertEqual(normalize_session_name("u-1/dma330/../rtl-gen"), "")


if __name__ == "__main__":
    unittest.main()
