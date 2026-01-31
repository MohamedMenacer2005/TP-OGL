"""
ORCHESTRATION LAYER - THE REFACTORING SWARM
ENSI Technical Specification 2025-2026

=== ARCHITECTURE DIAGRAM ===

START
  │
  ├─ Parse Arguments (--target_dir)
  │
  └─ Validate Directory
       │
       ├─ FAIL → Exit(1)
       │
       └─ SUCCESS
            │
            ├─────────────────────────────────────────┐
            │                                         │
            │  PHASE 1: AUDITOR (ONE TIME ONLY)       │
            │  ┌──────────────────────────────────┐   │
            │  │ auditor = AuditorAgent()         │   │
            │  │ audit_result = auditor.execute() │   │
            │  └──────────────────────────────────┘   │
            │                                         │
            │  Check: issues_found > 0?               │
            │    NO  → Exit(0) [Code is clean]        │
            │    YES → Continue                       │
            │                                         │
            └─────────────────────────────────────────┘
                          │
                          │ audit_result
                          ↓
            ╔═════════════════════════════════════════╗
            ║  SELF-HEALING LOOP (Max 10 iterations)  ║
            ║  ═════════════════════════════════════  ║
            ║                                         ║
            ║  ITERATION N:                           ║
            ║  ┌─────────────────────────────────┐    ║
            ║  │ PHASE 2: FIXER                  │    ║
            ║  │ ──────────────────────────────  │    ║
            ║  │ fixer = FixerAgent()            │    ║
            ║  │ fixer_result = fixer.execute(   │    ║
            ║  │   target_dir,                   │    ║
            ║  │   audit_result or judge_result │    ║
            ║  │ )                               │    ║
            ║  └─────────────────────────────────┘    ║
            ║            │                            ║
            ║            ↓                            ║
            ║  ┌─────────────────────────────────┐    ║
            ║  │ PHASE 3: JUDGE                  │    ║
            ║  │ ──────────────────────────────  │    ║
            ║  │ judge = JudgeAgent()            │    ║
            ║  │ judge_result = judge.execute()  │    ║
            ║  └─────────────────────────────────┘    ║
            ║            │                            ║
            ║            ├─ Check: all tests PASS?    ║
            ║            │                            ║
            ║            ├─ YES ──────→ Exit(0)       ║
            ║            │             [SUCCESS]      ║
            ║            │                            ║
            ║            └─ NO  ──────→ Loop?         ║
            ║                   iteration < 10?       ║
            ║                          │              ║
            ║                          ├─ YES → ↑↑↑  ║
            ║                          │        [Go to  ║
            ║                          │         next   ║
            ║                          │         Fixer] ║
            ║                          │              ║
            ║                          └─ NO  → Exit  ║
            ║                                 (1)     ║
            ║                              [FAILURE]   ║
            ║                                         ║
            ╚═════════════════════════════════════════╝


=== CRITICAL CONSTRAINTS ===

1. ✓ Auditor runs EXACTLY ONCE
   - Produces audit_result
   - If no issues → Exit immediately

2. ✓ Fixer never runs without Auditor results first

3. ✓ Judge only on Fixer output
   - NEVER calls Auditor again
   - Returns ONLY to Fixer on failure

4. ✓ Self-healing loop bounded
   - Maximum 10 iterations
   - Iteration counter tracked
   - Exit on: success OR max_iterations reached

5. ✓ Clean exit codes
   - sys.exit(0) = Success
   - sys.exit(1) = Failure

6. ✓ CLI compliance
   - --target_dir (required)
   - Validates directory existence
   - Uses exactly as provided


=== ORCHESTRATION STATE MACHINE ===

State          │ Condition              │ Next State      │ Action
───────────────┼────────────────────────┼─────────────────┼──────────────────
START          │ -                      │ AUDITOR         │ Parse args
AUDITOR        │ issues == 0            │ DONE_SUCCESS    │ Exit clean
AUDITOR        │ issues > 0             │ FIXER           │ Continue
FIXER          │ -                      │ JUDGE           │ Apply fixes
JUDGE          │ tests_pass == true     │ DONE_SUCCESS    │ Exit clean
JUDGE          │ tests_pass == false    │ LOOP_CHECK      │ Check iterations
LOOP_CHECK     │ iteration < 10         │ FIXER           │ Retry
LOOP_CHECK     │ iteration >= 10        │ DONE_FAILURE    │ Exit failure
DONE_SUCCESS   │ -                      │ -               │ sys.exit(0)
DONE_FAILURE   │ -                      │ -               │ sys.exit(1)


=== AGENT INTERFACES USED ===

Agent              │ Method     │ Input             │ Output
─────────────────  │ ──────────  │ ─────────────────  │ ──────────────────
AuditorAgent       │ execute()  │ target_dir        │ audit_result (dict)
FixerAgent         │ execute()  │ target_dir,       │ fixer_result (dict)
                   │            │ input_report      │
JudgeAgent         │ execute()  │ target_dir        │ judge_result (dict)


=== ORCHESTRATION PROPERTIES ===

✓ NO INFINITE LOOPS (bounded by max_iterations=10)
✓ NO HIDDEN RECURSION (explicit loop with counter)
✓ NO AGENT MODIFICATION (only calls existing interfaces)
✓ NO PROMPT ENGINEERING (delegated to agents)
✓ NO LOGGING LOGIC (delegated to logger utility)
✓ NO TOOL IMPLEMENTATIONS (delegated to tool layer)
✓ COMPLIANT WITH ENSI SPEC (3 agents, correct flow, clean exit)
"""
