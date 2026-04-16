# Customs Brain — Architecture

## Overview
Customs Brain is a multi-agent AI system for automated customs document processing.

## Data Flow
```
Upload → Backend → Redis Queue → Worker → Agent Pipeline → PostgreSQL → Frontend
```

## Agent Pipeline
```
ExtractionAgent
    └── HSCodeAgent
            └── WorldGeneratorAgent
                    └── ComplianceAgent
                            └── DutyAgent
                                    └── DebateAgent
                                            └── MetaAgent
                                                    └── OutputAgent
                                                            └── ReportAgent
```
