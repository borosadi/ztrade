# Architecture Decision Records (ADRs)

This directory contains all architectural decisions made for the Ztrade trading system.

## What is an ADR?

An Architecture Decision Record (ADR) captures an important architectural decision made along with its context and consequences. Each ADR describes:
- The **context** that led to the decision
- The **decision** itself
- The **rationale** behind it
- **Consequences** and tradeoffs
- **Implementation status**

## ADR Index

| ADR | Title | Date | Status |
|-----|-------|------|--------|
| [ADR-001](ADR-001-asset-based-architecture.md) | Asset-Based vs Task-Based Agent Architecture | 2025-11-07 | ✅ Decided |
| [ADR-002](ADR-002-multi-source-sentiment.md) | Multi-Source Sentiment Analysis Integration | 2025-11-07 | ✅ Implemented |
| [ADR-003](ADR-003-performance-tracking.md) | Performance Tracking for Sentiment Sources | 2025-11-07 | ✅ Implemented |
| [ADR-004](ADR-004-continuous-trading-loops.md) | Continuous Autonomous Trading Loops | 2025-11-08 | ✅ Implemented |

## Quick Links

- **Agent Architecture**: See [ADR-001](ADR-001-asset-based-architecture.md) for why we use asset-based agents
- **Sentiment Analysis**: See [ADR-002](ADR-002-multi-source-sentiment.md) for multi-source sentiment implementation
- **Performance Metrics**: See [ADR-003](ADR-003-performance-tracking.md) for sentiment tracking system
- **Continuous Trading**: See [ADR-004](ADR-004-continuous-trading-loops.md) for loop infrastructure

## Creating a New ADR

When making a significant architectural decision:

1. Copy the template below
2. Create a new file: `ADR-XXX-descriptive-name.md`
3. Fill in all sections
4. Update this README with the new entry

### ADR Template

```markdown
# ADR-XXX: [Short Title]

**Date**: YYYY-MM-DD
**Status**: [Proposed | Decided | Implemented | Superseded]

## Decision

[What is the decision?]

## Context

[What is the issue/situation that led to this decision?]

## Rationale

[Why did we make this decision? What alternatives were considered?]

## Consequences

[What are the positive and negative consequences of this decision?]

## Implementation

[How is/will this be implemented? What files/components are affected?]

## Future Considerations

[What future enhancements or changes might be needed?]
```
