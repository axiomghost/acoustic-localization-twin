# Decision Log

**Project:** Acoustic Source Localization Digital Twin  
Records architectural and algorithmic decisions with rationale. Updated as decisions are made.

---

## DEC-001 — Visualization: PyVista over Open3D
**Date:** 2026-06-18  
**Decision:** Use PyVista for 3D visualization in Phase 1.  
**Rationale:** PyVista has first-class mesh terrain support, built-in ellipsoid
primitives for confidence ellipse rendering, and a Pythonic live-update API
(`plotter.update()`). Open3D excels at point-cloud processing which is not the
core task here.  
**Consequence:** Phase 2 (UE5) replaces PyVista entirely; engine is unaffected.

---

## DEC-002 — IPC: Atomic JSON file over sockets/MQTT
**Date:** 2026-06-18  
**Decision:** Engine writes state to `shared/current_state.json` atomically each
tick (write-to-tmp, `os.replace()`). PyVista and Streamlit read it independently.  
**Rationale:** Zero broker dependencies, no threading conflicts between processes,
ships in hours. MQTT would be cleaner architecturally but adds a broker dependency
for a 12-day solo build. Can be upgraded later.  
**Consequence:** ~1-second dashboard refresh lag acceptable for portfolio demo.

---

## DEC-003 — Scenario config: YAML + Pydantic v2
**Date:** 2026-06-18  
**Decision:** Scenarios defined as YAML files, loaded and validated via Pydantic v2 models.  
**Rationale:** YAML is more readable than JSON for nested structures (sensor lists,
path waypoints). Pydantic gives free validation and clear error messages. Config
stays as data, not code — new scenarios require no Python changes.  
**Consequence:** Any scenario can be added by writing a YAML file. Public repo ships
civilian configs only.

---

## DEC-004 — Localization algorithm: Gauss-Newton TDOA
**Date:** 2026-06-18  
**Decision:** Implement linearized Gauss-Newton solver for TDOA hyperbolic intersection
as the baseline localization algorithm.  
**Rationale:** Well-understood, closed-form Jacobian, converges in <10 iterations
for typical sensor geometries, produces a covariance matrix directly usable for
confidence ellipse. Equivalent to Chan-Ho linearization. Alternative (Spherical
Interpolation / SRP-PHAT) deferred — can be plugged in via the `Localizer` Protocol.  
**Consequence:** Localizer is defined as a Protocol interface — alternative algorithms
can be swapped by config without touching engine orchestration.

---

## DEC-005 — Confidence estimation: Linearized covariance (CRLB proxy)
**Date:** 2026-06-18  
**Decision:** Estimate position covariance as `(J^T J)^{-1} * sigma_r^2` where J
is the TDOA Jacobian at the estimated position.  
**Rationale:** This is the Fisher Information Matrix inverse — a CRLB proxy. It
gives a theoretically grounded uncertainty bound without requiring Monte Carlo.
Chi-squared threshold for 95% CI in 2D: 5.991 (2 degrees of freedom).  
**Consequence:** Ellipse size is meaningful: sources near array edges or in poor
geometry (high GDOP) will show larger ellipses, which is correct behavior.

---

## DEC-007 — Localizer: weighted LS with correct TDOA noise covariance
**Date:** 2026-06-18
**Decision:** Replace unweighted Gauss-Newton with weighted GN using the correct
TDOA noise covariance matrix C = sigma_r^2 * M, M = I + 1*1^T.
**Rationale:** Each TDOA is toa[i+1] - toa[0], so all measurements share
sensor-0's noise — they are correlated, not independent. The unweighted solver
underestimates position covariance by ~2x, producing confidence ellipses that
are too small (73% coverage instead of 95%). The correct M^{-1} via
Sherman-Morrison is I - (1/N)*ones, giving the true MLE solution and the
correct Fisher Information Matrix. Caught and confirmed by the Monte Carlo
coverage test in Step 3.
**Consequence:** Ellipse sizes increase slightly (~sqrt(2) on axes) but now
correctly represent 95% confidence. The fix is validated by the coverage test.

---

## DEC-006 — Abstract interfaces: TerrainBase, PropagationModel, Localizer
**Date:** 2026-06-18  
**Decision:** Define Protocol/ABC for exactly three components: TerrainBase,
PropagationModel, Localizer. Everything else is concrete.  
**Rationale:** These three are the components Phase 1.5 and Phase 2 will swap
(hilly terrain, wind-affected propagation, alternative localization methods).
Abstracting more would be premature.  
**Consequence:** New terrain types, propagation models, or localization algorithms
require implementing one Protocol — no changes to engine orchestration.
