# SEC Filings Monitoring System - Project Structure

```
sec-insights/
├── backend/
│   ├── data_collection/          # SEC RSS and EDGAR API integration
│   │   ├── rss_fetcher.py        # RSS feed monitoring
│   │   ├── edgar_client.py       # EDGAR API client with aj0strow/edgar
│   │   └── filing_downloader.py  # Downloads complete filings
│   │
│   ├── analysis/                 # LLM-based analysis components
│   │   ├── models.py             # OpenRouter model integration
│   │   ├── filing_analyzer.py    # Extract key insights from filings
│   │   ├── entity_linker.py      # Connect related filings/entities
│   │   └── event_detector.py     # Detect significant events
│   │
│   ├── storage/                  # Cloud storage integration
│   │   ├── gcs_client.py         # Google Cloud Storage client
│   │   ├── db_client.py          # Database client for structured data
│   │   └── archive_manager.py    # Manages archiving of filings
│   │
│   └── api/                      # API endpoints
│       ├── app.py                # FastAPI application
│       ├── routers/              # API route definitions
│       ├── stream.py             # SSE streaming implementation
│       └── rss_generator.py      # Generate RSS feeds from analysis
│
├── frontend/                     # Framer-based frontend
│   ├── components/               # Reusable UI components
│   ├── pages/                    # Application pages
│   └── utils/                    # Helper functions
│
├── infra/                        # Infrastructure as code
│   ├── terraform/                # Terraform configurations for GCP
│   └── kubernetes/               # K8s deployment manifests
│
└── scripts/                      # Utility scripts
    ├── setup.sh                  # Project setup script
    └── deploy.sh                 # Deployment script
```