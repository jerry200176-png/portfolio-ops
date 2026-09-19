import unittest
from agent_graph.deploy_observe import note_portfolio_ops_has_no_product_deploy

class DeployObserveTests(unittest.TestCase):
    def test_portfolio_ops_deploy_authority_disabled(self):
        note = note_portfolio_ops_has_no_product_deploy()
        self.assertFalse(note["graph_production_deploy_authority"])
        self.assertIsNone(note["product_deploy_path"])

if __name__ == "__main__":
    unittest.main()
