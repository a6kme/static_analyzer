import tempfile
import unittest

from api.evaluate.generate_dataset import GenerateDataset
from api.src.models import GithubRepo


class TestDatasetCreation(unittest.TestCase):

    def test_create_dataset(self):
        """
            Test the creation of a dataset
        """
        repo = GithubRepo(name='juice-shop', owner='juice-shop')
        pr_ids = [40]

        # TODO: Unable to use VCR with current design. docker.get_client() does not work with VCR
        # Think about how the code can be refactored to make it testable [ It feels like GenerateDataset.generate
        # is doing too much and should be broken down into smaller functions ]
        # with test_vcr.use_cassette('github_create_dataset.yaml'):

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            GenerateDataset(repo=repo, pr_ids=pr_ids,
                            dataset_file_path=temp_file.name).generate()

            # Ensure that there are entries in the dataset
            with open(temp_file.name, 'r') as f:
                assert (len(f.readlines()) > 0)
