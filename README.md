# ERC-8350 G4 — Independent External Security Review (evidence repository)

Reviewer-controlled evidence repository for the **independent external Solidity
security review** requested in
[AwareLiquid/AgentMemoryState#11](https://github.com/AwareLiquid/AgentMemoryState/issues/11),
satisfying the evidence requirements enumerated in
[#22](https://github.com/AwareLiquid/AgentMemoryState/issues/22).

- **Candidate:** G4-rc1 — frozen commit `af5a75fb2db532fd5603554083d8895a825c2de2`
- **Reviewer:** Besmubsa (independent, pseudonymous; no compensation; no affiliation)
- **Result:** no Critical / High / Medium findings; 4 Informational; intake dispositions LOW-1, LOW-2, INFO-1, INFO-2 concurred with; G4-R-012 mitigation verified.

## Contents

| Path | Purpose |
|------|---------|
| `reports/erc8350-g4-external-review.md` | Full review report (canonical artifact; SHA-256 in `external-review.json`) |
| `external-review.json` | Completed record per `audits/g4/external/external-review.template.json` |
| `evidence/vector_recompute.py` + `vector_recompute_output.txt` | From-scratch Python reimplementation of the golden-vector pipeline (10/10 PASS) |
| `evidence/evm_domain_check.py` + `evm_domain_output.txt` | Compiled Registry bytecode deployed and executed on py-evm; domain separator matches the vector |
| `evidence/slither/` + `slither_summary.txt` | Static analysis outputs (0.11.6, 102 detectors) with triage |
| `evidence/build_log.txt` | solc 0.8.24 compilation evidence (runtime contracts + deployment harness) |
| `evidence/DeployHarness.s.sol` | Build harness for `Deploy.s.sol` (import prefixes rewritten only; contract code unchanged) |

## Reproduction

The report's Section 4 lists every command. All evidence is regenerable from the
frozen commit; file digests are attested in the report's Section 3.

## Publication

- Report SHA-256: `822d2a3642fe9006945ba8bf074455da6b47b91352c1992606c026ca4be74f6b`
- Published (ISO-8601): `2026-10-24T06:30:00Z`


## Small paid technical tasks

I am open to clearly scoped, small technical tasks such as bot prototypes, Python automation, documentation improvements, reproducible bug reports, and focused code-review support. See [SERVICES.md](SERVICES.md) for scope, starting prices, and how to request a quote.
