variable "project_id" {
  description = "Google Cloud Project ID"
  type        = string
}

variable "region" {
  description = "Google Cloud region"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "Google Cloud zone"
  type        = string
  default     = "us-central1-a"
}

variable "bucket_prefix" {
  description = "Prefix for GCS bucket names"
  type        = string
  default     = "sec-insights"
}

variable "api_image_url" {
  description = "URL of the API container image"
  type        = string
}