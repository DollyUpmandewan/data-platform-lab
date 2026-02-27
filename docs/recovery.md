# Service continuity and recovery

Collection failures are recorded against the affected dates. Data that fails quality assessment is held separately for review and does not replace an accepted dataset.

## What happens during a disruption

| Event | Pipeline response | Effect on published data |
|---|---|---|
| Temporary source timeout or service error | Automatic retries with increasing delays, up to four collection attempts | Existing accepted data remains available |
| Persistent source failure | The affected date is recorded as failed | No new version is published for that date |
| Missing, duplicate or invalid data | The response is retained separately with failed quality-check results | The invalid response is withheld from publication |
| Unexpected daily fields | The schema check rejects the response | The existing data contract remains in effect |
| Storage or publication failure | The date is recorded as failed where reporting remains available | Previously published references remain in place |
| Failure affecting only part of a historical range | Other dates continue through assessment | Successful dates can still be published |

Storage requests also receive bounded retries for temporary failures. Persistent errors end the attempt rather than retrying indefinitely.

## Recovery outcome

Affected dates can be reprocessed after the underlying problem is resolved. Recovered data passes the same quality checks as the original collection. Publication occurs only after the accepted replacement is stored successfully.

A recovered date has a successful result, a complete set of passing checks and a published reference to the accepted data. Earlier failed attempts remain distinguishable from the recovered result.

## Understanding availability

A failed replacement does not invalidate a previous successful version. For a date that has never been published, a failed collection means that date remains unavailable. A historical range can therefore contain both available and unavailable dates until recovery completes.

Quality reports identify dates and failed checks. If storage is entirely unavailable, saving the report can also fail; application logs provide the remaining record of the attempt. Recovery preserves the publication boundary even when reporting is interrupted.

## Data separation

Original responses, accepted data and rejected data are stored separately. Synthetic demonstration data has its own publication references. Logs contain operational metadata rather than credentials or source-response bodies.
