variable "credentials" {
  description = "My Credentials"
  default     = "./my-creds.json"
}

variable "project" {
  description = "Project"
  default     = "shondazenithcloud"

}

variable "region" {
  description = "Region"
  default     = "us-central1"

}

variable "location" {
  description = "Project Location"
  default     = "US"

}

variable "bq_dataset_name" {
  description = "My BiqQuery Dataset Name"
  default     = "example_dataset"

}

variable "gcs_bucket_name" {
  description = "My Storage Bucket Name"
  default     = "shondazenithcloud-terra-bucket"

}

variable "gcs_storage_class" {
  description = "Bucket Storage Class"
  default     = "STANDARD"
}