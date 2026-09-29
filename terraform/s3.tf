resource "aws_s3_bucket" "landing_zone" {
  bucket = "insurance-lakehouse-landing-zone-vitor-dev"
}

resource "aws_s3_bucket_server_side_encryption_configuration" "landing_zone_encryption" {
  bucket = aws_s3_bucket.landing_zone.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}