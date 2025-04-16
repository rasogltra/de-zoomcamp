# Setting up infrastructure on GCP with Terraform

Configure it -> Initialize -> Plan -> Apply -> Destroy

### Prerequisites
* Install Terraform (https://developer.hashicorp.com/terraform)
* Install gCloud CLI

### Setup GCP Service Account
Setup a service account and name the account `terraform-runner`. Assign `Storage admin` and `BigQuery admin` roles. Create and download the JSON key file.

#### Managing keys
To authenicate Terraform with GCP: `gcloud auth application-default login`. Here you can authenicate with your Google account. After success authentication, credentials will be stored locally and Terraform will be able to use them automatically.

#### Terraform Configuration

1. Add configurations. See [Main.tf](https://github.com/rasogltra/de-zoomcamp/blob/main/week1/terraform/main.tf).
2. Run `terraform init`
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
