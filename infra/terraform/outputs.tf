output "api_url" {
  value       = google_cloud_run_service.api.status[0].url
  description = "URL of the SEC Insights API"
}

output "raw_filings_bucket" {
  value       = google_storage_bucket.raw_filings.name
  description = "Name of the raw filings bucket"
}

output "analyses_bucket" {
  value       = google_storage_bucket.analyses.name
  description = "Name of the analyses bucket"
}

output "events_bucket" {
  value       = google_storage_bucket.events.name
  description = "Name of the events bucket"
}