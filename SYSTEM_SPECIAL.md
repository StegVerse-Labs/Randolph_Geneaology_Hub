# SYSTEM SPEC — Randolph Sovereign Identity & Genealogy Engine (RSIGE)

## Data Models

### Person Object
```json
{
  "id": "<hash>",
  "publicName": "Nellie Althea Cash",
  "privateFields": {
    "fullName": "...",
    "birthCert": "...",
    "dnaHash": "xxxx",
    "documentsEncrypted": []
  },
  "parents": ["id1","id2"],
  "children": ["id3","id4"],
  "visibility": {
     "publicProfile": true,
     "publicRelationMap": true,
     "dnaMatchingAllowed": false
  }
}
