import unittest

from api.evaluate.generate_llm_reviews import \
    get_patch_line_to_hunk_line_mapping


class TestUtils(unittest.TestCase):

    def test_get_patch_line_to_hunk_line_mapping(self):
        with open('api/tests/fixtures/patch.diff') as f:
            patch = f.read()
        mapping = get_patch_line_to_hunk_line_mapping(patch)
        self.assertEqual(mapping[12], 74)
        self.assertEqual(mapping[22], 147)
        self.assertEqual(mapping[41], 216)
