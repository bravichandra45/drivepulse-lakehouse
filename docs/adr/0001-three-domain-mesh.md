# ADR 0001 — Three-domain Unity Catalog mesh

**Status:** accepted
**Date:** 2026-06-25

## Context
DrivePulse must demonstrate a data mesh, not a single lake. A mesh needs believable domain
ownership. Too few domains = not a mesh; too many = fictional ownership.

## Decision
Use exactly three catalogs aligned to three real teams: `prod_telematics` (IoT),
`prod_policy` (Underwriting), `prod_claims` (Claims Ops). Logical sub-domains (vehicle ref,
crash/safety, environment, documents) roll up under the owning team's catalog or are
federated; they do not get their own catalogs.

## Consequences
- Clear ownership and a credible mesh story.
- Cross-domain analytics (`mart_claim_360`) live in the consuming team's catalog.
- Federated sources (weather/vPIC/OSM) stay external and are queried in place.
