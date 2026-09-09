import pytest
from src.schemas.manifest import RawSheetPayload, StatementType
from src.ingestion.resolver import resolve_statement_conflicts, _prompt_user_choice


def test_resolve_no_conflicts():
    """Verify that sheets pass through untouched when all required statements are uniquely identified."""
    sheets = [
        RawSheetPayload(source_filename="doc.pdf", sheet_name="Page 1", detected_type=StatementType.BALANCE_SHEET),
        RawSheetPayload(source_filename="doc.pdf", sheet_name="Page 2", detected_type=StatementType.INCOME_STATEMENT),
        RawSheetPayload(source_filename="doc.pdf", sheet_name="Page 3", detected_type=StatementType.CASH_FLOW_STATEMENT),
    ]
    resolved = resolve_statement_conflicts(sheets, interactive=False)
    assert len(resolved) == 3
    assert resolved[0].detected_type == StatementType.BALANCE_SHEET
    assert resolved[1].detected_type == StatementType.INCOME_STATEMENT
    assert resolved[2].detected_type == StatementType.CASH_FLOW_STATEMENT


def test_resolve_duplicate_non_interactive():
    """Verify that duplicate candidate statements raise ValueError in non-interactive mode."""
    sheets = [
        RawSheetPayload(source_filename="doc.pdf", sheet_name="Page 1", detected_type=StatementType.BALANCE_SHEET),
        RawSheetPayload(source_filename="doc.pdf", sheet_name="Page 2", detected_type=StatementType.BALANCE_SHEET),
        RawSheetPayload(source_filename="doc.pdf", sheet_name="Page 3", detected_type=StatementType.INCOME_STATEMENT),
        RawSheetPayload(source_filename="doc.pdf", sheet_name="Page 4", detected_type=StatementType.CASH_FLOW_STATEMENT),
    ]
    with pytest.raises(ValueError, match="Ambiguous candidates for BALANCE_SHEET"):
        resolve_statement_conflicts(sheets, interactive=False)


def test_resolve_duplicate_interactive(monkeypatch):
    """Verify human-in-the-loop choice selection for resolving duplicate candidates."""
    sheets = [
        RawSheetPayload(source_filename="doc.pdf", sheet_name="Page 1", raw_grid=[["Balance Sheet A"]], detected_type=StatementType.BALANCE_SHEET),
        RawSheetPayload(source_filename="doc.pdf", sheet_name="Page 2", raw_grid=[["Balance Sheet B"]], detected_type=StatementType.BALANCE_SHEET),
        RawSheetPayload(source_filename="doc.pdf", sheet_name="Page 3", raw_grid=[["Income Stmt"]], detected_type=StatementType.INCOME_STATEMENT),
        RawSheetPayload(source_filename="doc.pdf", sheet_name="Page 4", raw_grid=[["Cash Flow"]], detected_type=StatementType.CASH_FLOW_STATEMENT),
    ]
    # Simulate user choosing option '2' (Page 2) for duplicate BALANCE_SHEET
    inputs = iter(["2"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    resolved = resolve_statement_conflicts(sheets, interactive=True)
    
    # Page 2 remains BALANCE_SHEET; Page 1 is demoted to UNKNOWN
    assert sheets[1].detected_type == StatementType.BALANCE_SHEET
    assert sheets[0].detected_type == StatementType.UNKNOWN


def test_resolve_missing_non_interactive():
    """Verify that missing required statements raise ValueError in non-interactive mode."""
    sheets = [
        RawSheetPayload(source_filename="doc.pdf", sheet_name="Page 1", detected_type=StatementType.BALANCE_SHEET),
        RawSheetPayload(source_filename="doc.pdf", sheet_name="Page 2", detected_type=StatementType.UNKNOWN),
    ]
    with pytest.raises(ValueError, match="Required statement 'INCOME_STATEMENT' could not be identified"):
        resolve_statement_conflicts(sheets, interactive=False)


def test_resolve_missing_no_unassigned_sheets():
    """Verify exception when a statement is missing and there are zero UNKNOWN sheets to assign."""
    sheets = [
        RawSheetPayload(source_filename="doc.pdf", sheet_name="Page 1", detected_type=StatementType.BALANCE_SHEET),
    ]
    with pytest.raises(ValueError, match="no unassigned sheets/pages are available"):
        resolve_statement_conflicts(sheets, interactive=False)


def test_resolve_missing_interactive_assign(monkeypatch):
    """Verify human-in-the-loop assignment of an UNKNOWN sheet to a missing statement."""
    sheets = [
        RawSheetPayload(source_filename="doc.pdf", sheet_name="Page 1", raw_grid=[["Assets..."]], detected_type=StatementType.BALANCE_SHEET),
        RawSheetPayload(source_filename="doc.pdf", sheet_name="Page 2", raw_grid=[["Revenue..."]], detected_type=StatementType.UNKNOWN),
        RawSheetPayload(source_filename="doc.pdf", sheet_name="Page 3", raw_grid=[["Operating Cash..."]], detected_type=StatementType.CASH_FLOW_STATEMENT),
    ]
    # Missing INCOME_STATEMENT -> User selects option 1 (Page 2) to assign it to INCOME_STATEMENT
    inputs = iter(["1"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    resolved = resolve_statement_conflicts(sheets, interactive=True)

    assert sheets[1].detected_type == StatementType.INCOME_STATEMENT


def test_resolve_missing_interactive_abort(monkeypatch):
    """Verify human-in-the-loop abort option when a required statement is missing."""
    sheets = [
        RawSheetPayload(source_filename="doc.pdf", sheet_name="Page 1", raw_grid=[["Assets..."]], detected_type=StatementType.BALANCE_SHEET),
        RawSheetPayload(source_filename="doc.pdf", sheet_name="Page 2", raw_grid=[["Random Notes"]], detected_type=StatementType.UNKNOWN),
    ]
    # Missing INCOME_STATEMENT -> User selects option 2 (Abort pipeline)
    inputs = iter(["2"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    with pytest.raises(RuntimeError, match="Pipeline stopped by user"):
        resolve_statement_conflicts(sheets, interactive=True)


def test_prompt_user_choice_invalid_then_valid(monkeypatch):
    """Test user prompt retry logic when invalid text or out-of-bounds numbers are entered."""
    inputs = iter(["invalid", "99", "2"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    choice = _prompt_user_choice(3, "Choose option")
    assert choice == 2
