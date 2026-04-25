---
# bugfix-3: diagnostician fills the next-stage routing here
# (planning / executing / testing / acceptance / done / requirement_review / ready_for_execution).
# `harness next` reads this field first; if empty, falls back to text markers
# ("Route: xxx" / "harness next -> xxx"); otherwise default sequence.
route_to: ""
---

# Regression Decision

## 1. Decision Status

- `analysis`
- `confirmed`
- `rejected`
- `cancelled`
- `converted`

## 2. Final Notes

- Record why the issue was confirmed or why it was not accepted as a problem.

## 3. Follow-Up

- If confirmed, record which requirement update or change was created.
- If cancelled or rejected, record why it was closed.
