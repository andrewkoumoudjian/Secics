# SEC Insights Tool

A comprehensive system for monitoring, analyzing, and visualizing SEC filings using AI/ML.

## Overview

SEC Insights Tool monitors SEC RSS feeds and EDGAR filings, analyzes them using language models, and provides a real-time dashboard of insights, events, and entity relationships.

## Features

- **Real-time Monitoring**: Tracks SEC RSS feeds for new filings
- **AI-Powered Analysis**: Uses OpenRouter models to extract insights from filings
- **Event Detection**: Identifies significant events like management changes, acquisitions, etc.
- **Entity Linking**: Connects related entities across multiple filings
- **Interactive Dashboard**: Framer-based visualization with filtering and search
- **Cloud-Native**: Fully deployable on Google Cloud Platform

## Architecture

- **Backend**: Python FastAPI application for data processing and API endpoints
- **Frontend**: Framer-based web interface
- **Storage**: Google Cloud Storage for raw filings and analysis results
- **Infrastructure**: Terraform for deployment automation

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 14+
- Docker
- Google Cloud SDK
- Terraform

### Environment Setup

1. Clone the repository:

```bash
git clone https://github.com/yourusername/sec-insights.git
cd sec-insights
```

2. Set up environment variables:

```bash
export GOOGLE_CLOUD_PROJECT=your-gcp-project-id
export OPENROUTER_API_KEY=your-openrouter-api-key
```

3. Install dependencies:

```bash
pip install -r requirements.txt
cd frontend && npm install
```

### Local Development

1. Start the backend:

```bash
python -m backend.api.app
```

2. Start the frontend:

```bash
cd frontend && npm start
```

### Deployment

To deploy to Google Cloud:

```bash
./scripts/deploy.sh
```

## Usage

### API Endpoints

- `GET /filings`: List recent filings
- `GET /filings/{filing_id}`: Get a specific filing
- `GET /filings/{filing_id}/analysis`: Get analysis for a filing
- `GET /events/critical`: Get critical events
- `GET /stream`: SSE stream for real-time updates

### Dashboard

Access the dashboard at `https://<your-frontend-url>/` after deployment.

## License

MIT