# AegisBilling Synthetic RAG Dataset

This folder contains a legally clean synthetic dataset for the AegisBilling.ai
demo. It is intended to be used with the Synthea `100 Sample Synthetic Patient
Records, CSV` download as the only external dataset.

No real patient data is included. No AMA CPT, X12, UB-04, CDT, or payer-owned
licensed code descriptions are copied here. Procedure identifiers are synthetic
and exist only for the demo.

## What To Add From Synthea

Place the Synthea CSV sample you downloaded here:

```text
data/synthea_csv/
```

Recommended files from Synthea:

- `patients.csv`
- `conditions.csv`
- `encounters.csv`
- `procedures.csv`
- `observations.csv`
- `medications.csv`

If your Synthea zip has more files, that is fine. The demo only needs a small
subset.

## Folder Layout

```text
data/
  policies/          Synthetic payer policy documents for RAG retrieval
  claims/            Synthetic claim packages in human-readable text
  clinical_notes/    Synthetic physician notes and reports
  supporting_docs/   Synthetic attachments that may or may not be submitted
  synthea_csv/       Put the downloaded Synthea CSV files here
```

## Demo Scenarios

1. `claim_pt_001_missing_docs.txt`
   - Physical therapy claim with medically consistent diagnosis and procedure.
   - Missing referral, initial PT evaluation, and progress report.
   - Expected result: block before submission and return a missing-documents checklist.

2. `claim_pt_002_complete.txt`
   - Same type of therapy claim, but all required attachments are present.
   - Expected result: ready to send to insurance.

3. `claim_img_001_missing_prior_auth.txt`
   - Advanced imaging claim with diagnosis support but no prior authorization.
   - Expected result: block before submission and request authorization document.

4. `claim_lab_001_clean.txt`
   - Lab panel claim with required diagnosis support.
   - Expected result: ready to send to insurance.

## Intended RAG Flow

1. Ingest `data/policies/*.txt` into a vector database.
2. Parse a claim from `data/claims/*.txt`.
3. Retrieve policy chunks using payer, procedure identifiers, diagnosis codes,
   quantity, and service type.
4. Compare retrieved rules with attached documents listed in the claim.
5. Return a concrete checklist of missing requirements before insurance
   submission.

