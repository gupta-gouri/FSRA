from typing import Dict, List, Optional, Set
from src.schemas.manifest import RawSheetPayload, StatementType

# Mandatory statements required to proceed with audit tie-outs
REQUIRED_STATEMENTS = [
    StatementType.BALANCE_SHEET,
    StatementType.INCOME_STATEMENT,
    StatementType.CASH_FLOW_STATEMENT,
]


def resolve_statement_conflicts(
    sheets: List[RawSheetPayload],
    required_types: Optional[List[StatementType]] = None,
    interactive: bool = True
) -> List[RawSheetPayload]:
    """
    Audits classified sheets for missing statements or duplicate candidates.
    If conflicts exist:
      - Interactively prompts the user via CLI to choose or assign sheets.
      - If non-interactive, raises a ValueError detailing the conflict.
    """
    if required_types is None:
        required_types = REQUIRED_STATEMENTS

    # Group sheets by their detected type
    type_map: Dict[StatementType, List[RawSheetPayload]] = {st: [] for st in StatementType}
    for s in sheets:
        type_map[s.detected_type].append(s)

    resolved_sheets = list(sheets)

    # -------------------------------------------------------------
    # 1. RESOLVE DUPLICATE CANDIDATES
    # -------------------------------------------------------------
    for stmt_type in required_types:
        candidates = type_map[stmt_type]
        if len(candidates) > 1:
            print(f"\n[!] AMBIGUITY DETECTED: Multiple sheets classified as '{stmt_type.value}':")
            for idx, c in enumerate(candidates, start=1):
                preview = " | ".join(str(row[0]) for row in c.raw_grid[:3] if row and row[0])
                print(f"  [{idx}] File: {c.source_filename} | Sheet/Page: {c.sheet_name} (Preview: {preview[:60]}...)")

            if not interactive:
                raise ValueError(f"Ambiguous candidates for {stmt_type.value}. Human confirmation required.")

            choice = _prompt_user_choice(len(candidates), f"Select the correct sheet for {stmt_type.value}")
            selected_candidate = candidates[choice - 1]

            # Demote non-selected candidates to UNKNOWN
            for c in candidates:
                if c != selected_candidate:
                    c.detected_type = StatementType.UNKNOWN
            
            # Update type map
            type_map[stmt_type] = [selected_candidate]

    # -------------------------------------------------------------
    # 2. RESOLVE MISSING STATEMENTS
    # -------------------------------------------------------------
    unknown_candidates = [s for s in resolved_sheets if s.detected_type == StatementType.UNKNOWN]

    for stmt_type in required_types:
        if len(type_map[stmt_type]) == 0:
            print(f"\n[!] MISSING STATEMENT: No sheet classified as '{stmt_type.value}'.")
            
            if not unknown_candidates:
                raise ValueError(f"Cannot proceed: '{stmt_type.value}' is missing and no unassigned sheets/pages are available.")

            print("Available unassigned sheets/pages:")
            for idx, u in enumerate(unknown_candidates, start=1):
                preview = " | ".join(str(row[0]) for row in u.raw_grid[:3] if row and row[0])
                print(f"  [{idx}] File: {u.source_filename} | Sheet/Page: {u.sheet_name} (Preview: {preview[:60]}...)")
            print(f"  [{len(unknown_candidates) + 1}] Abort pipeline (statement is truly missing)")

            if not interactive:
                raise ValueError(f"Required statement '{stmt_type.value}' could not be identified.")

            choice = _prompt_user_choice(
                len(unknown_candidates) + 1, 
                f"Select which sheet should be mapped to '{stmt_type.value}'"
            )

            if choice == len(unknown_candidates) + 1:
                raise RuntimeError(f"Pipeline stopped by user: Missing required statement '{stmt_type.value}'.")

            selected_sheet = unknown_candidates.pop(choice - 1)
            selected_sheet.detected_type = stmt_type
            type_map[stmt_type] = [selected_sheet]

    return resolved_sheets


def _prompt_user_choice(max_option: int, prompt_text: str) -> int:
    """Helper to safely prompt for user CLI integer selection."""
    while True:
        user_input = input(f">> {prompt_text} (Enter 1-{max_option}): ").strip()
        if user_input.isdigit():
            val = int(user_input)
            if 1 <= val <= max_option:
                return val
        print(f"Invalid entry. Please enter a number between 1 and {max_option}.")