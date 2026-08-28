from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
UNITS = ROOT / "automation" / "systemd"


class GovernanceTimerTests(unittest.TestCase):
    def test_service_is_read_only_and_uses_canonical_autopilot(self):
        service = (UNITS / "portfolio-ops-governance-autopilot.service").read_text(encoding="utf-8")
        self.assertIn("Type=oneshot", service)
        self.assertIn("/home/jerry/workspace/portfolio-ops/scripts/governance-autopilot.sh", service)
        self.assertIn("--policy /home/jerry/workspace/portfolio-ops/governance/autonomy-automation.yaml", service)
        self.assertIn("--scan-root /home/jerry/workspace", service)
        self.assertIn("--scan-root /home/jerry/wt", service)
        self.assertIn("--scan-root /home/jerry", service)
        self.assertIn("NoNewPrivileges=yes", service)
        self.assertIn("ProtectHome=read-only", service)
        self.assertNotIn("--apply-safe-cleanup", service)

    def test_timer_is_persistent_but_not_continuously_running(self):
        timer = (UNITS / "portfolio-ops-governance-autopilot.timer").read_text(encoding="utf-8")
        self.assertIn("OnCalendar=*-*-* 03:15:00 Asia/Taipei", timer)
        self.assertIn("Persistent=true", timer)
        self.assertIn("RandomizedDelaySec=15min", timer)
        self.assertIn("Unit=portfolio-ops-governance-autopilot.service", timer)

    def test_installer_refuses_different_existing_units_and_defaults_to_disabled(self):
        installer = (ROOT / "scripts" / "install-governance-autopilot-timer.sh").read_text(encoding="utf-8")
        self.assertIn("cmp -s", installer)
        self.assertIn("--enable-now", installer)
        self.assertIn("installed but not enabled", installer)
        self.assertNotIn("systemctl --user enable --now", installer.split("if [[", 1)[0])
        for forbidden in ("git reset", "git clean", "git merge", "git rebase", "rm -rf"):
            self.assertNotIn(forbidden, installer)


if __name__ == "__main__":
    unittest.main()
