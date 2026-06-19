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
tick (write-to-tmp, `os.replace()`). PyVista and the Rich panel read it independently.  
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

## DEC-008 — Algorithm extension: impulsive event localization (crack + blast fusion)
**Date:** 2026-06-19  
**Decision:** Plan a dedicated algorithm extension for impulsive acoustic events
(e.g., a single transient impulse from a fixed source) using two-source TDOA fusion.  
**Rationale:** A continuous-emitter moving source (current model) and an impulsive
fixed-source event are different physical scenarios requiring different algorithms:

  - **Muzzle blast only (pure TDOA):** single impulsive wave from a fixed point.
    Sensors measure TOA of the wavefront. TDOA between sensors triangulates back
    to the source. This already works with the current engine — stationary source,
    one tick, done.

  - **Crack + blast fusion (two-source model):** a supersonic projectile generates
    two simultaneous acoustic events: (1) the muzzle blast radiating from the fixed
    shooter position, (2) the ballistic shockwave (N-wave / Mach cone) sweeping
    past sensors along the bullet trajectory. Each sensor records two distinct
    arrival times. The algorithm must: deinterleave the two arrival sets, fit the
    Mach-cone geometry to crack arrivals to extract bullet azimuth and elevation,
    then fuse with blast TDOA to recover shooter position and bullet trajectory.
    This is significantly more complex than single-source TDOA.

**Scope for this project:** None. Steps 9-11 are explicitly out of scope for this
repository. This repo is a public civilian portfolio artifact and must not contain
impulsive event or weapons-adjacent content anywhere — not in code, comments,
configs, or git history.

**Consequence:** Steps 9-11 will be executed in a separate private repository when
required. The Protocol interfaces (Localizer, PropagationModel) are already designed
for drop-in extension — no changes to this repo will be needed to support that work.
The private repo can import the engine as a library or fork it independently.

---

## DEC-009 — Range-dependent per-sensor timing noise model
**Date:** 2026-06-19
**Decision:** Model each sensor's arrival-time noise std as linear in source-sensor
range: `sigma_i = ref_std * (dist_i / ref_distance)` (`timing_std_from_range`).
**Rationale:** Received amplitude falls as 1/r, so SNR_linear ~ 1/r^2, and a matched
filter's time-delay CRLB gives std(tau) ~ 1/sqrt(SNR_linear) ~ r. This is a
defensible first-order model that makes sensors genuinely heterogeneous. The previous
display-only SNR model `max(0, 40 - 20log10 d)` saturated to 0 dB beyond 100 m, which
on a 300 m array made every sensor equal — hiding the entire point of weighting.
**Consequence:** Localization error now depends on which sensors are close to the
source. This is the substrate for DEC-010 (weighting) and foreshadows the GCC-PHAT
measurement model (Phase 1.5 step D1). The exact ref_std / ref_distance are simulation
parameters; the real hardware noise-vs-SNR curve remains an open deployment question.

---

## DEC-010 — Localizer: maximum-ratio (inverse-variance) weighting
**Date:** 2026-06-19
**Decision:** Generalize the weighted Gauss-Newton solver from equal-variance
(`W = M^{-1}`) to the true inverse measurement covariance `W = C_r^{-1}`, where
`C_r = c^2 (diag(var[1:]) + var[0]*ones)` is built from per-sensor variances. When
per-sensor variances are supplied, `estimate()` returns the position covariance
directly in m^2 (no separate sigma_r scaling — a single scalar can no longer be
factored out once variances differ).
**Rationale:** This is maximum-ratio combining / soft-decision weighting: each sensor
contributes in proportion to its reliability. Equal-weight LS is equal-gain combining
and is provably suboptimal under heterogeneous noise. Monte Carlo confirms the gain:
with one sensor degraded x10, equal-weight RMSE rises to 17 cm while MRC holds at
~4.8 cm (11 dB array gain); coverage stays at 95%. The equal-variance path is
preserved (`sensor_var=None`) so prior behaviour and tests are unchanged.
**Consequence:** The engine now feeds per-sensor variances (from DEC-009) into the
localizer and passes `sigma_r=1.0` to `confidence_ellipse` since the covariance is
already scaled. Documented and taught in concepts.ipynb section 8 (MRC bridge).

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
