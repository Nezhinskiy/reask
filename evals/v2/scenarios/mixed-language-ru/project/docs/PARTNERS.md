# POS partners

| Partner | File on SFTP | Delimiter | Notes |
|---|---|---|---|
| brewline | `brewline/brewline-YYYY-MM-DD.csv` | `,` | Cloud POS, UTF-8. |
| kedr-pos | `kedr-pos/kedr_YYYYMMDD.csv` | `;` | Desktop POS. New export ("Kassa 7") since 2026-10-30; the old export was ASCII-only (transliterated store names). |
| lumen-pos | `lumen-pos/lumen_YYYYMMDD.csv` | `,` | Cloud POS, UTF-8. |

Columns (all partners): `receipt_id`, `store_id`, `store_name`, `ts`, `amount`, `stamps`.

`store_name` is shown to customers in the app and is what finance matches against the café
contracts when it reconciles stamps at month end.
