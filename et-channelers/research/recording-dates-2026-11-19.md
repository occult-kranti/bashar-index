# Publication dates in the November 19 latest-20+ selection

The frozen selection contains 1,976 regular uploads from 101 YouTube channels. **1,579 recordings can be placed in 2026, 177 in 2025 and 201 in earlier years.** The other 19 have estimated windows that cross a year boundary. Individual channels contribute up to 20 public, completed Videos-tab uploads across any date or duration. The resulting distribution describes the selected recordings. [Interactive timeline](../dashboard/collection/timeline.html) · [Annual chart](../dashboard/collection/recording-dates-yearly.png)

| Evidence used | Recordings | What the date describes |
|---|---:|---|
| Watch-page publication field | 49 | Calendar day in YouTube's datePublished or publishDate field |
| Availability metadata | 1,530 | UTC day of the timestamp saved by the extractor for public availability |
| Upload-day fallback | 0 | Extractor upload_date is used when it is the strongest available date |
| Relative listing age | 397 | An inclusive date window inferred from the label on the creator's Videos tab and the UTC time at which that listing was saved |

The channel and video IDs must match across the frozen selection and saved metadata. Each row retains its publication, availability and upload fields separately, the visible age label, observation clock, public source link and source checksum. A conflicting date at the strongest available evidence level stays unresolved. These dates can differ from the date of the session described in a recording. [Recording-level CSV](../dashboard/collection/recording-dates.csv) · [Machine-readable evidence](../dashboard/collection/recording-dates.json)

For a listing of *n* units ago, the estimated interval runs from *n + 1* units before observation to *n* units before observation. Weeks use seven days, months use 365.2425/12 days and years use 365.2425 days. Labels expressed in days or longer receive one day of padding on each side for display rounding. The upper bound is capped at the observation time. In the 1,579 recordings with both a metadata date and a visible age label, all 1,579 metadata dates fell inside the derived window. This measures agreement on the observed overlap. It cannot establish the exact publication day of the remaining 397.

A recording enters a calendar bin only when both ends of the interval lie within it. That places 1,957 recordings by year and 1,694 by month. The remaining 282 monthly intervals appear in a separate ambiguous row. For October and November 2026 the assignable totals are 305 and 331. November observations stop on the 19th, and each creator's latest-20 window covers a different span. [Monthly CSV](../dashboard/collection/dates-by-month.csv) · [Yearly CSV](../dashboard/collection/dates-by-year.csv)

The date report was built at 23:58 UTC on November 19 using the metadata catalog and 449 matching retained job sidecars. It required no new requests to YouTube. Membership is pinned by selection SHA-256 `adb76d392fa9eded77e03fb41687a630fb82a17fb3de21af504092710b08fd01`. [Evidence builder](../pipeline/regular_recording_dates.py) · [Offline dashboard renderer](../pipeline/collection_metadata_timeline.py)
