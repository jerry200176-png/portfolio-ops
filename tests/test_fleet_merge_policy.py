from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class FleetMergePolicyTests(unittest.TestCase):
    def test_autonomy_agent_is_operator(self):
        policy = (ROOT / "governance/AUTONOMY_POLICY.md").read_text(
            encoding="utf-8"
        )
        normalized_policy = " ".join(policy.split())
        fleet = (ROOT / "docs/fleet-merge-policy.md").read_text(encoding="utf-8")
        contract = (ROOT / "governance/company-agent-contract.yaml").read_text(
            encoding="utf-8"
        )
        self.assertIn("docs/fleet-merge-policy.md", policy)
        self.assertIn("Authoring a migration is engineering work", policy)
        self.assertIn("A routine reversible", policy)
        self.assertIn("product T0–T3 classes", policy)
        self.assertIn("complete difference from the actual production", policy)
        self.assertIn("Author migration files, database functions, and constraints", policy)
        self.assertIn("Run migrations locally / in authorized isolated test or staging", policy)
        self.assertIn("Production migration execution or protected activation", policy)
        self.assertIn("classify any push-triggered release", policy)
        self.assertNotIn("Deploy itself is not a Founder gate", policy)
        self.assertIn("continue separable containment", policy)
        self.assertIn("Do not invent deadlines, payment states", normalized_policy)
        self.assertIn("Production **data** mutation", policy)
        self.assertIn("**No**", policy.split("Production **data** mutation")[1][:120])
        self.assertIn("Founder approval", policy.split("Production **data** mutation")[1][:180])
        self.assertIn("Founder-protected R3 execution", policy)
        self.assertIn("Stop if recovery or", fleet)
        self.assertIn("Close a GitHub issue", policy)
        self.assertIn("Gmail trash / delete", policy)
        self.assertIn("**No**", policy.split("Gmail trash / delete")[1][:120])
        self.assertIn("gh pr merge --squash --delete-branch", fleet)
        self.assertIn("Do not `--admin`", fleet)
        self.assertIn(
            "eligible_low_risk_reversible_squash_merge",
            contract,
        )
        self.assertIn("founder_approval_required", contract)
        self.assertIn("machine_banned", contract)
        self.assertIn("required_status_checks_before_merge", contract)
        self.assertIn("weaken_tests_assertions_allowlists_or_security_controls", contract)
        agent_owned = contract.split("agent_owns_with_evidence:", 1)[1].split(
            "founder_approval_required:", 1
        )[0]
        founder_gated = contract.split("founder_approval_required:", 1)[1]
        self.assertIn("migration_file_authoring", agent_owned)
        self.assertIn("local_or_authorized_isolated_migration_testing", agent_owned)
        self.assertNotIn("deploy_via_product_path_when_risk_allows", agent_owned)
        self.assertIn("routine_reversible_deploy_via_authorized_product_path", agent_owned)
        self.assertNotIn("controlled_r3_execution_via_product_path", agent_owned)
        self.assertNotIn("credential_rotation_via_committed_workflow", agent_owned)
        self.assertIn("production_migration_execution", founder_gated)
        self.assertIn("protected_production_activation", founder_gated)
        self.assertIn("breaking_schema_contract_material_blast_radius", founder_gated)
        self.assertIn("billing_payment_semantics", founder_gated)
        self.assertIn("material_reservation_product_policy", founder_gated)
        security = (ROOT / "docs/security-boundaries.md").read_text(encoding="utf-8")
        self.assertIn("classify the full", security)
        self.assertIn("exact effects are already authorized", security)
        constitution = (ROOT / "governance/COMPANY_CONSTITUTION.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("exact effects are already authorized", constitution)
        self.assertIn("require explicit Founder approval before execution", constitution)
        self.assertIn("Founder approves production execution", constitution)
        skill = (ROOT / ".claude/skills/portfolio-maintain/SKILL.md").read_text(
            encoding="utf-8"
        )
        normalized_skill = " ".join(skill.split())
        execute = (ROOT / ".claude/skills/portfolio-maintain/modes/execute.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "Migration authoring and authorized isolated testing are Agent-owned",
            normalized_skill,
        )
        self.assertIn("Production migration execution", execute)
        self.assertIn("continue separable containment", execute)
        overlay = (ROOT / "governance/PORTFOLIO_AGENT_CONTRACT.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Migration authoring and local or authorized isolated migration testing", overlay)
        self.assertIn("full production-to-candidate risk", overlay)
        self.assertIn("committed reversible workflows", overlay)
        self.assertIn("exact effects are", overlay)
        pr_template = (ROOT / "docs/templates/draft-pr-description.md").read_text(
            encoding="utf-8"
        )
        normalized_pr_template = " ".join(pr_template.split())
        self.assertIn(
            "Production migration execution and product-defined protected activation require explicit Founder approval",
            normalized_pr_template,
        )
        retry_loop = (ROOT / "docs/verify-retry-loop.md").read_text(encoding="utf-8")
        normalized_retry_loop = " ".join(retry_loop.split())
        self.assertIn(
            "Reversible migration authoring and isolated testing may use the normal engineering loop",
            normalized_retry_loop,
        )
        maintainer = (ROOT / ".claude/agents/repo-maintainer.md").read_text(
            encoding="utf-8"
        )
        normalized_maintainer = " ".join(maintainer.split())
        self.assertIn("This is a role handoff, not a Founder gate", normalized_maintainer)
        settings = (ROOT / ".claude/settings.json").read_text(encoding="utf-8")
        self.assertNotIn("merge_pull_request", settings)
        self.assertNotIn("send_message", settings)
        self.assertIn("delete_message", settings)


if __name__ == "__main__":
    unittest.main()
