# Narrator Scope

Agent:

- `relatorio_html`

Mission:

- Build the HTML report for the Savannah River study using the established project visual pattern
- Consume only the figures and structured context produced by the Analyst
- Keep the report honest about current completeness

Reservoir scope:

- Hartwell
- Russell
- Thurmond

Editorial framing:

- Final report target: Savannah River mainstem behavior, pressures, and sediment linkage
- Sediment-study focal reservoir: Thurmond
- Hartwell and Russell must appear as operational context inside the river narrative, not as protagonists
- If the system is still incomplete, the HTML must say so plainly
- If collection returned less than the 20-year target window, the HTML must say so plainly
- The report should distinguish between the 20-year target horizon and the actual years returned by each source

Expected content blocks:

- river scope and study framing
- pollutant-pressure and environmental context on the river
- river coverage status
- reservoir operations only as explanatory context
- Thurmond-focused interpretation bridge to sediment context
- data gaps and restrictions
- methods and provenance notes

Visual rule:

- Keep the current project layout and style stable
- Change content, figures, metrics, and narrative only

Do not:

- Do not publish a three-reservoir conclusion if the EDA still has only Thurmond normalized
- Do not hide missing Hartwell or Russell coverage behind generic wording
- Do not imply 20-year coverage when the collected record is shorter

Final output target:

- `docs/clarks-hill/index.html`

Escalate if:

- the EDA handoff does not clearly separate system-wide evidence from Thurmond-only evidence
