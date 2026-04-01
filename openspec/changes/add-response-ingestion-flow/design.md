# Design: Response Ingestion Flow

## Summary

Response ingestion sits between dispatch preparation and result capture.

It converts a raw provider response into:
- a canonical captured response file under the request bundle
- normalized generated artifacts under the linked result bundle
- synchronized result and dispatch metadata

## Parsing Strategy

The ingestion layer should be transport-aware first and fallback-tolerant second.

- OpenAI Responses API: extract `output_text` or message output content
- OpenAI-compatible chat completions: extract `choices[].message.content`
- Anthropic Messages API: extract `content[].text`
- manual markdown/text: treat the raw file as the assistant response body

The assistant response is then parsed against the benchmark delivery contract:
- section headings identify `Files`, `Benchmark Report`, and `Known Limitations`
- file entries follow the canonical `### FILE: relative/path.ext` contract
- the benchmark report uses one fenced `json` block

## Safety

Ingestion should preserve provenance and avoid silent corruption.

- never write files outside `generated/`
- keep authoritative benchmark identity fields owned by the existing result record
- keep the raw captured response in the dispatch bundle even after normalization
- tolerate partially structured responses by storing the full assistant markdown even when file extraction is incomplete
