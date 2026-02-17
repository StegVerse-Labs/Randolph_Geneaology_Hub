# Randolph Genealogy Hub
## Data Schema v1.0

This schema defines the required structure for all Individual identity records.

No individual file may deviate from this schema.

---

## Required Fields

### # Identity
Canonical_ID:
Full_Legal_Name:
Known_As:
Birth:
Death:
Burial:
Primary_Locations:

---

### # Parentage
Father_CID:
Mother_CID:
Evidence_Level:

---

### # Marriages
Spouse_CID:
Marriage_Date:
Marriage_Location:
Source_ID:

---

### # Children
Child_CID:

---

### # Migration Timeline
Year:
Location:
Source_ID:

---

### # Military Record
Unit:
Rank:
Service_Dates:
Source_ID:

---

### # Occupation

---

### # Source Citations
Source_ID:
Description:
Evidence_Level:

---

### # Evidence Confidence Rating
A / B / C / D

---

## Schema Enforcement Rules

1. No missing Canonical_ID.
2. No parent-child links without Source_ID.
3. No free-text citation without Source_ID.
4. No unsourced lineage promotion.
5. No structural deviation.

---

Schema Version: 1.0
