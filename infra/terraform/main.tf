provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# Create Cloud Storage buckets
resource "google_storage_bucket" "raw_filings" {
  name          = "${var.bucket_prefix}-raw-filings"
  location      = var.region
  force_destroy = false
  
  versioning {
    enabled = true
  }
  
  lifecycle_rule {
    condition {
      age = 365 # days
    }
    action {
      type = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }
}

resource "google_storage_bucket" "analyses" {
  name          = "${var.bucket_prefix}-analyses"
  location      = var.region
  force_destroy = false
  
  lifecycle_rule {
    condition {
      age = 90 # days
    }
    action {
      type = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }
}

resource "google_storage_bucket" "events" {
  name          = "${var.bucket_prefix}-events"
  location      = var.region
  force_destroy = false
}

resource "google_storage_bucket" "entities" {
  name          = "${var.bucket_prefix}-entities"
  location      = var.region
  force_destroy = false
}

resource "google_storage_bucket" "links" {
  name          = "${var.bucket_prefix}-links"
  location      = var.region
  force_destroy = false
}

# Cloud Run service for API
resource "google_cloud_run_service" "api" {
  name     = "sec-insights-api"
  location = var.region
  
  template {
    spec {
      containers {
        image = var.api_image_url
        
        env {
          name  = "GOOGLE_CLOUD_PROJECT"
          value = var.project_id
        }
        
        env {
          name  = "BUCKET_PREFIX"
          value = var.bucket_prefix
        }
        
        env {
          name  = "OPENROUTER_API_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.openrouter_api_key.secret_id
              key  = "latest"
            }
          }
        }
        
        resources {
          limits = {
            cpu    = "1000m"
            memory = "512Mi"
          }
        }
      }
      
      service_account_name = google_service_account.api_service_account.email
      
      # Better concurrency for streaming connections
      container_concurrency = 80
      timeout_seconds = 300
    }
  }
  
  traffic {
    percent         = 100
    latest_revision = true
  }
  
  autogenerate_revision_name = true
}

# Service account for the API
resource "google_service_account" "api_service_account" {
  account_id   = "sec-insights-api-sa"
  display_name = "SEC Insights API Service Account"
}

# IAM bindings for service account
resource "google_storage_bucket_iam_member" "api_storage_admin" {
  for_each = {
    raw_filings = google_storage_bucket.raw_filings.name
    analyses    = google_storage_bucket.analyses.name
    events      = google_storage_bucket.events.name
    entities    = google_storage_bucket.entities.name
    links       = google_storage_bucket.links.name
  }
  
  bucket = each.value
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.api_service_account.email}"
}

# Secret for API key
resource "google_secret_manager_secret" "openrouter_api_key" {
  secret_id = "openrouter-api-key"
  
  replication {
    automatic = true
  }
}

# Allow Cloud Run service to access the secret
resource "google_secret_manager_secret_iam_member" "api_secret_access" {
  secret_id = google_secret_manager_secret.openrouter_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.api_service_account.email}"
}

# Cloud Scheduler job for periodic tasks
resource "google_cloud_scheduler_job" "daily_processing" {
  name             = "sec-insights-daily-processing"
  description      = "Trigger daily processing of SEC filings"
  schedule         = "0 4 * * *" # Run at 4 AM every day
  time_zone        = "America/New_York"
  attempt_deadline = "320s"
  
  http_target {
    http_method = "POST"
    uri         = "${google_cloud_run_service.api.status[0].url}/admin/process_daily"
    
    oidc_token {
      service_account_email = google_service_account.api_service_account.email
    }
  }
}