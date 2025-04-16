# Setting up infrastructure on GCP with Terraform

Configure it -> Initialize -> Plan -> Apply -> Destroy

## Built With
* Terraform
* Google Cloud

### Prerequisites
* Setup a service account in Google Cloud

### Terraform for GCP

1. Install provider, copy and paste provider Terraform configuration. Where ```bash my-project-id ``` comes from GCP dashboard. See [Main.tf](https://github.com/rasogltra/de-zoomcamp/blob/main/week1/terraform/main.tf).
2. Run ```bash terraform init ```
3. Append a new bucket in Google cloud storage service. See [Main.tf](https://github.com/rasogltra/de-zoomcamp/blob/main/week1/terraform/main.tf).
```bash
resource "google_storage_bucket" "auto-expire" {
  name          = "auto-expiring-bucket"
  location      = "US"
  force_destroy = true

  lifecycle_rule {
    condition {
      age = 3
    }
    action {
      type = "Delete"
    }
  }

  lifecycle_rule {
    condition {
      age = 1
    }
    action {
      type = "AbortIncompleteMultipartUpload"
    }
  }
}
```
Where ```bash auto-expire & name ``` should be change to a unique name.

4. Run ```bash terraform plan ``` Check GCP for bucket.
5. Run ```bash terraform destory ```
6. Modify Main.tf by creating variables in [Variables.tf](https://github.com/rasogltra/de-zoomcamp/blob/main/week1/terraform/variables.tf).
9. Run ```bash terraform apply ``` to see changes.
