## Problem Statement

Build an AI-powered restaurant recommendation system that allows users to choose:
- location,
- numeric budget (cost for two),
- cuisine preferences,
- minimum rating,
- additional preferences.

The system should return grounded restaurant recommendations from available dataset records with concise explanations.

## Data Contract and Location Scope

The UI location dropdown is backed by `GET /v1/cities` and currently serves 30 normalized locations, including:
- banashankari
- bannerghatta road
- basavanagudi
- bellandur
- brigade road
- brookefield
- btm
- church street
- electronic city
- frazer town
- hsr
- indiranagar
- jayanagar
- jp nagar
- kalyan nagar
- kammanahalli
- koramangala 4th block
- koramangala 5th block
- koramangala 6th block
- koramangala 7th block
- lavelle road
- malleshwaram
- marathahalli
- mg road
- new bel road
- old airport road
- rajajinagar
- residency road
- sarjapur road
- whitefield

## Expected Recommendation Behavior

- Success with matches:
  - Return `200` and list of recommendations with metadata.
- No matching restaurants:
  - Return `200` with `recommendations: []` and a guidance `summary`.
  - Avoid frontend-breaking `404` for no-match user inputs.

## Observed Validation Samples

Recent validated examples using present locations:
- banashankari -> Onesta, The Blue Wagon - Kitchen, Stoned Monkey
- hsr -> Tipsy Bull - The Bar Exchange, Shift, Opus Food Stories
- indiranagar -> Delhi Highway, Burma Burma, Toit
