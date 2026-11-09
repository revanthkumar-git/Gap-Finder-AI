"""
Comprehensive Automated Regression Test Suite for Nexqile - WealthAgent API
"""
import sys
import os
import unittest
from fastapi.testclient import TestClient

# Ensure backend root is in PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app

client = TestClient(app)

class TestNexqileWealthAgentAPI(unittest.TestCase):

    def test_01_root_and_demo_credentials(self):
        resp = client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Nexqile - WealthAgent", resp.json()["portal"])

        demo_resp = client.get("/api/auth/demo-credentials")
        self.assertEqual(demo_resp.status_code, 200)
        self.assertEqual(len(demo_resp.json()["accounts"]), 5)

    def test_02_authentication_all_roles(self):
        roles = [
            ("client@nexqile.demo", "client"),
            ("advisor@nexqile.demo", "advisor"),
            ("sponsor@nexqile.demo", "sponsor"),
            ("participant@nexqile.demo", "participant"),
            ("admin@nexqile.demo", "admin"),
        ]
        for email, expected_role in roles:
            resp = client.post("/api/auth/login", json={"email": email, "password": "Demo@123"})
            self.assertEqual(resp.status_code, 200, f"Login failed for {email}")
            data = resp.json()
            self.assertIn("access_token", data)
            self.assertEqual(data["user"]["role_name"], expected_role)

            # Test /me endpoint
            me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {data['access_token']}"})
            self.assertEqual(me_resp.status_code, 200)
            self.assertEqual(me_resp.json()["email"], email)

    def test_03_dashboard_endpoints(self):
        login_resp = client.post("/api/auth/login", json={"email": "client@nexqile.demo", "password": "Demo@123"})
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # KPIs
        kpis = client.get("/api/dashboard/kpis", headers=headers)
        self.assertEqual(kpis.status_code, 200)
        self.assertGreater(kpis.json()["net_worth"], 2000000)

        # Performance series across multiple intervals
        for r in ["1M", "3M", "6M", "1Y", "3Y", "ALL"]:
            perf = client.get(f"/api/dashboard/performance?range={r}", headers=headers)
            self.assertEqual(perf.status_code, 200)
            self.assertGreater(len(perf.json()), 0)

        # Allocation, Cashflow, Risk profile, Actions
        alloc = client.get("/api/dashboard/allocation", headers=headers)
        self.assertEqual(alloc.status_code, 200)
        self.assertGreater(len(alloc.json()), 0)

        cashflow = client.get("/api/dashboard/cashflow", headers=headers)
        self.assertEqual(cashflow.status_code, 200)

        risk = client.get("/api/dashboard/risk-profile", headers=headers)
        self.assertEqual(risk.status_code, 200)
        self.assertEqual(risk.json()["risk_score"], 72)

        actions = client.get("/api/dashboard/upcoming-actions", headers=headers)
        self.assertEqual(actions.status_code, 200)
        self.assertGreater(len(actions.json()), 0)

    def test_04_wealth_management_and_goals_crud(self):
        login_resp = client.post("/api/auth/login", json={"email": "client@nexqile.demo", "password": "Demo@123"})
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Accounts
        accs = client.get("/api/wealth/accounts", headers=headers)
        self.assertEqual(accs.status_code, 200)
        self.assertGreaterEqual(len(accs.json()), 4)

        # Holdings
        holdings = client.get("/api/wealth/holdings", headers=headers)
        self.assertEqual(holdings.status_code, 200)
        self.assertGreaterEqual(len(holdings.json()), 10)

        # Filtered Holdings
        eq_holdings = client.get("/api/wealth/holdings?asset_class=Equities", headers=headers)
        self.assertEqual(eq_holdings.status_code, 200)
        for h in eq_holdings.json():
            self.assertEqual(h["asset_class"], "Equities")

        # Goals CRUD
        new_goal = {
            "title": "Automated Unit Test Goal",
            "category": "Retirement",
            "target_amount": 100000.0,
            "current_amount": 25000.0,
            "target_date": "2030-01-01",
            "monthly_contribution": 500.0,
            "notes": "Test goal creation"
        }
        create_resp = client.post("/api/wealth/goals", json=new_goal, headers=headers)
        self.assertEqual(create_resp.status_code, 200)
        goal_id = create_resp.json()["id"]

        # Update Goal
        update_resp = client.put(f"/api/wealth/goals/{goal_id}", json={"current_amount": 30000.0}, headers=headers)
        self.assertEqual(update_resp.status_code, 200)
        self.assertEqual(update_resp.json()["current_amount"], 30000.0)

        # Delete Goal
        del_resp = client.delete(f"/api/wealth/goals/{goal_id}", headers=headers)
        self.assertEqual(del_resp.status_code, 200)

        # Scenarios
        scen_resp = client.get("/api/wealth/scenarios", headers=headers)
        self.assertEqual(scen_resp.status_code, 200)
        self.assertEqual(len(scen_resp.json()["scenarios"]), 3)

    def test_05_tax_estate_and_harvesting(self):
        login_resp = client.post("/api/auth/login", json={"email": "client@nexqile.demo", "password": "Demo@123"})
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        tax = client.get("/api/tax-estate/tax-summary", headers=headers)
        self.assertEqual(tax.status_code, 200)
        self.assertEqual(tax.json()["harvestable_unrealized_losses"], 18400.0)

        # Execute harvest
        harvest = client.post("/api/tax-estate/execute-harvest", headers=headers)
        self.assertEqual(harvest.status_code, 200)
        self.assertEqual(harvest.json()["status"], "Success")

        estate = client.get("/api/tax-estate/estate-summary", headers=headers)
        self.assertEqual(estate.status_code, 200)
        self.assertGreater(len(estate.json()["beneficiaries"]), 0)
        self.assertGreater(len(estate.json()["trusts"]), 0)

        phil = client.get("/api/tax-estate/philanthropy", headers=headers)
        self.assertEqual(phil.status_code, 200)
        self.assertIn("donor_advised_fund", phil.json())

    def test_06_retirement_and_participant(self):
        login_resp = client.post("/api/auth/login", json={"email": "sponsor@nexqile.demo", "password": "Demo@123"})
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        plan = client.get("/api/retirement/plan-overview", headers=headers)
        self.assertEqual(plan.status_code, 200)
        self.assertEqual(plan.json()["total_plan_assets"], 42500000.0)

        funds = client.get("/api/retirement/fund-lineup", headers=headers)
        self.assertEqual(funds.status_code, 200)
        self.assertGreaterEqual(len(funds.json()), 5)

        comp = client.get("/api/retirement/sponsor/compliance", headers=headers)
        self.assertEqual(comp.status_code, 200)
        self.assertEqual(comp.json()["status"], "In Full Compliance")

        # Participant Portal tests
        part_login = client.post("/api/auth/login", json={"email": "participant@nexqile.demo", "password": "Demo@123"})
        part_token = part_login.json()["access_token"]
        part_headers = {"Authorization": f"Bearer {part_token}"}

        part_me = client.get("/api/retirement/participant/me", headers=part_headers)
        self.assertEqual(part_me.status_code, 200)
        self.assertEqual(part_me.json()["current_balance"], 248500.0)

        # Update contribution
        update_contrib = client.post("/api/retirement/participant/update-contribution?contribution_percent=10.5", headers=part_headers)
        self.assertEqual(update_contrib.status_code, 200)
        self.assertEqual(update_contrib.json()["new_rate"], 10.5)

        edu = client.get("/api/retirement/education/modules", headers=part_headers)
        self.assertEqual(edu.status_code, 200)
        self.assertEqual(len(edu.json()), 7)

    def test_07_advisor_workstation(self):
        login_resp = client.post("/api/auth/login", json={"email": "advisor@nexqile.demo", "password": "Demo@123"})
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        metrics = client.get("/api/advisor/metrics", headers=headers)
        self.assertEqual(metrics.status_code, 200)
        self.assertEqual(metrics.json()["total_aum"], 148500000.0)

        clients = client.get("/api/advisor/clients", headers=headers)
        self.assertEqual(clients.status_code, 200)
        self.assertGreaterEqual(len(clients.json()), 4)

        # Client profile dossier
        c_id = clients.json()[0]["id"]
        profile = client.get(f"/api/advisor/clients/{c_id}", headers=headers)
        self.assertEqual(profile.status_code, 200)
        self.assertIn("accounts", profile.json())

        # Drift rebalancing & execution
        drift = client.get("/api/advisor/rebalancing/drift", headers=headers)
        self.assertEqual(drift.status_code, 200)
        self.assertIn("asset_classes", drift.json())

        rebal = client.post("/api/advisor/rebalancing/execute", headers=headers)
        self.assertEqual(rebal.status_code, 200)
        self.assertEqual(rebal.json()["status"], "Submitted")

    def test_08_communication_documents_reports_admin(self):
        login_resp = client.post("/api/auth/login", json={"email": "admin@nexqile.demo", "password": "Demo@123"})
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Messages
        msgs = client.get("/api/comm/messages", headers=headers)
        self.assertEqual(msgs.status_code, 200)

        # Meetings
        meets = client.get("/api/comm/meetings", headers=headers)
        self.assertEqual(meets.status_code, 200)

        # Tasks
        tasks = client.get("/api/comm/tasks", headers=headers)
        self.assertEqual(tasks.status_code, 200)
        if tasks.json():
            t_id = tasks.json()[0]["id"]
            up_task = client.put(f"/api/comm/tasks/{t_id}", json={"status": "Completed"}, headers=headers)
            self.assertEqual(up_task.status_code, 200)

        # Documents
        docs = client.get("/api/documents", headers=headers)
        self.assertEqual(docs.status_code, 200)

        # Reports
        reports = client.get("/api/reports", headers=headers)
        self.assertEqual(reports.status_code, 200)

        # Admin Users & Audits
        users = client.get("/api/admin/users", headers=headers)
        self.assertEqual(users.status_code, 200)

        audits = client.get("/api/admin/audit-events", headers=headers)
        self.assertEqual(audits.status_code, 200)
        self.assertGreater(len(audits.json()), 0)

        health = client.get("/api/admin/system-health", headers=headers)
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["status"], "Operational")

    def test_09_admin_interactive_actions(self):
        login_resp = client.post("/api/auth/login", json={"email": "admin@nexqile.demo", "password": "Demo@123"})
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Fetch users
        users = client.get("/api/admin/users", headers=headers).json()
        target_user = users[0]
        user_id = target_user["id"]

        # 1. Update Profile
        up_profile = client.put(
            f"/api/admin/users/{user_id}/profile",
            json={"full_name": target_user["full_name"], "email": target_user["email"]},
            headers=headers
        )
        self.assertEqual(up_profile.status_code, 200)
        self.assertEqual(up_profile.json()["status"], "success")

        # 2. Reset Password
        reset_pw = client.put(
            f"/api/admin/users/{user_id}/reset-password",
            json={"new_password": "Demo@123TempPassword"},
            headers=headers
        )
        self.assertEqual(reset_pw.status_code, 200)
        self.assertEqual(reset_pw.json()["status"], "success")

        # Reset it back to standard demo password
        client.put(
            f"/api/admin/users/{user_id}/reset-password",
            json={"new_password": "Demo@123"},
            headers=headers
        )

        # 3. Test Maintenance actions
        actions = ["wal-checkpoint", "clear-cache", "prune-sessions", "rotate-keys"]
        for act in actions:
            m_resp = client.post(f"/api/admin/maintenance/{act}", headers=headers)
            self.assertEqual(m_resp.status_code, 200, f"Maintenance action {act} failed")
            self.assertEqual(m_resp.json()["status"], "success")

if __name__ == "__main__":
    unittest.main()
