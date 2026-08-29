"""
Root Math Engine Orchestrator
"""
from decimal import Decimal
from typing import Dict, Any, List
from backend.src.schemas.manifest import IngestionManifest, StatementType
from backend.src.schemas.statements import StandardFinancialStatement
from backend.src.verification.assertions import run_complete_audit_suite
from backend.src.verification.guardrails import run_input_guardrails_suite


class MathEngine:
    def __init__(
        self,
        statements: Dict[StatementType, StandardFinancialStatement],
        manifest: IngestionManifest
    ):
        self.statements = statements
        self.manifest = manifest
        self.metadata = manifest.metadata

    def run_guardrails(self) -> List[Dict[str, Any]]:
        return run_input_guardrails_suite(self.statements)

    def run_deterministic_math_engine(self) -> List[Dict[str, Any]]:
        return run_complete_audit_suite(self.statements)

    def generate_structured_audit_report(self) -> Dict[str, Any]:
        """Generates the full audit report with PASS / FLAGGED / REJECTED status classifications."""

        RULE_FAILURE_MAP = {
            "MATH_01": "REJECTED", "MATH_02": "REJECTED", "MATH_03": "REJECTED", "MATH_04": "REJECTED",
            "MATH_05": "REJECTED", "MATH_06": "REJECTED", "MATH_07": "REJECTED", "MATH_08": "REJECTED",
            "MATH_09": "REJECTED", "MATH_10": "REJECTED", "MATH_11": "REJECTED",
            "TIEOUT_01": "REJECTED", "TIEOUT_02": "REJECTED", "TIEOUT_03": "REVIEW REQUIRED", "TIEOUT_04": "REJECTED",
            "PY_01": "REJECTED", "PY_02": "REJECTED", "PY_03": "REJECTED", "PY_04": "REJECTED", "PY_05": "REJECTED",
            "NOTE_01": "REJECTED", "NOTE_02": "REJECTED", "NOTE_03": "REJECTED", "NOTE_04": "REJECTED",
            "NOTE_05": "REJECTED", "NOTE_06": "REJECTED", "NOTE_07": "REJECTED", "NOTE_08": "REJECTED",
            "IS_GUARD_01": "REVIEW REQUIRED", "IS_GUARD_03": "REVIEW REQUIRED", "BS_GUARD_01": "REJECTED",
            "CF_GUARD_02": "REVIEW REQUIRED", "CF_GUARD_03": "REVIEW REQUIRED", "NOTE_GUARD_02": "REJECTED"
        }

        math_flags = self.run_deterministic_math_engine()
        guardrails = self.run_guardrails()

        engagement = {
            "client_name": self.metadata.client_name or "Unknown Entity",
            "period": self.metadata.period_ended or "CY",
            "currency": self.metadata.currency or "USD",
            "review_stage": "CY_Final"
        }

        procedures = []
        findings = []
        step_counter = 1
        failed_conclusions = []

        # 1. Process 28 Math Assertions
        for flag in math_flags:
            rule_id = flag.get("rule_id", "")
            is_pass = (flag.get("status") == "PASS")
            failure_conclusion = RULE_FAILURE_MAP.get(rule_id, "REJECTED")

            if not is_pass:
                failed_conclusions.append(failure_conclusion)
                findings.append({
                    "id": f"FINDING-{len(findings)+1:03d}",
                    "rule_id": rule_id,
                    "severity": "CRITICAL" if failure_conclusion == "REJECTED" else "HIGH",
                    "description": flag.get("description"),
                    "expected": flag.get("expected"),
                    "actual": flag.get("actual"),
                    "difference": flag.get("difference"),
                    "status": "OPEN",
                    "resolution": f"Rule failure: {failure_conclusion}. Reconcile underlying ledger accounts."
                })

            procedures.append({
                "step": step_counter,
                "category": flag.get("category"),
                "procedure": flag.get("description"),
                "reference": rule_id,
                "status": "PASS" if is_pass else ("FAIL" if failure_conclusion == "REJECTED" else "FLAGGED"),
                "issue": None if is_pass else f"Discrepancy of {flag.get('difference'):,}: Expected {flag.get('expected'):,}, Actual {flag.get('actual'):,}",
                "resolution": "no action required." if is_pass else f"Audit Action: {failure_conclusion}"
            })
            step_counter += 1

        # 2. Process Guardrails
        for g in guardrails:
            rule_id = g.get("rule_id", "")
            is_pass = (g.get("status") == "PASS")
            failure_conclusion = RULE_FAILURE_MAP.get(rule_id, "REVIEW REQUIRED")

            if not is_pass:
                failed_conclusions.append(failure_conclusion)

            procedures.append({
                "step": step_counter,
                "category": g.get("category"),
                "procedure": g.get("rule_name"),
                "reference": rule_id,
                "status": "PASS" if is_pass else "FLAGGED",
                "issue": None if is_pass else g.get("message"),
                "resolution": "no action required." if is_pass else f"Audit Action: {failure_conclusion}"
            })
            step_counter += 1

        # Overall Status Determination
        if "REJECTED" in failed_conclusions:
            overall_status = "REJECTED"
            conclusion_text = "Audit status REJECTED due to failure in critical deterministic footing / tie-out rules."
        elif "REVIEW REQUIRED" in failed_conclusions:
            overall_status = "REVIEW REQUIRED"
            conclusion_text = f"{len(findings)} exceptions flagged requiring auditor review."
        else:
            overall_status = "CLEARED"
            conclusion_text = f"All {len(procedures)} procedures completed cleanly with status CLEARED."

        return {
            "engagement": engagement,
            "conclusion": {
                "overall_status": overall_status,
                "total_procedures_run": len(procedures),
                "procedures_passed": len(procedures) - len(failed_conclusions),
                "text": conclusion_text
            },
            "procedures": procedures,
            "findings": findings
        }