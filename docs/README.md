# HouseFlavor documentation

Start here.
This folder is the map of how HouseFlavor works, why it is built the way it is, and where it is going.

## Documents

| Doc | What it covers |
|---|---|
| [architecture.md](architecture.md) | Layers, data flow, the scoring engine, the data model, and diagrams. The living picture of what is built. |
| [scoring-contract.md](scoring-contract.md) | The authoritative spec: objective gates, the taste-axis and style model, the observation schema, the vision prompt, and the match mapping. |
| [roadmap.md](roadmap.md) | The four MVP phases in context, plus the future phases and cross-cutting work that are not yet planned in detail. |
| [decisions.md](decisions.md) | The decision log: the significant technical choices and why they were made. |
| [plans/](plans/README.md) | Detailed, actionable plans for the four MVP phases (A to D) and the cross-cutting neutrality requirement. |

## How they relate

The scoring contract is the specification.
The architecture doc is the implementation as it stands, and it links to the contract for the parts still being built.
The plans break the MVP into phases with acceptance criteria.
The roadmap looks past the MVP.
The decision log explains the choices that shaped all of the above.

## Reading order

For a first pass: [architecture.md](architecture.md), then [scoring-contract.md](scoring-contract.md), then [roadmap.md](roadmap.md).
To understand a specific choice: [decisions.md](decisions.md).
To pick up build work: the relevant plan under [plans/](plans/README.md).
