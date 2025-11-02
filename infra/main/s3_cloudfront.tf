########################################
# Static site S3 bucket
########################################

resource "aws_s3_bucket" "static_site" {
  bucket = "genonaut-${var.env}-static-site"

  tags = {
    Name = "genonaut-${var.env}-static-site"
    Env  = var.env
  }
}

# Block public ACLs etc. (we'll still allow CloudFront via policy below)
resource "aws_s3_bucket_public_access_block" "static_site" {
  bucket = aws_s3_bucket.static_site.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 needs to be able to serve index.html without content-type weirdness
# (The new AWS provider defaults are fine, so we don't need website hosting mode;
# CloudFront will handle directory -> index.html routing.)

########################################
# CloudFront Origin Access Control (OAC)
########################################

resource "aws_cloudfront_origin_access_control" "static_site_oac" {
  name                              = "genonaut-${var.env}-static-site-oac"
  description                       = "OAC for genonaut ${var.env} static site"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

########################################
# CloudFront Distribution
########################################

resource "aws_cloudfront_distribution" "static_site" {
  enabled             = true
  comment             = "genonaut ${var.env} static site"
  default_root_object = "index.html"

  origin {
    domain_name              = aws_s3_bucket.static_site.bucket_regional_domain_name
    origin_id                = "s3-static-origin-${var.env}"
    origin_access_control_id = aws_cloudfront_origin_access_control.static_site_oac.id
  }

  default_cache_behavior {
    target_origin_id       = "s3-static-origin-${var.env}"
    viewer_protocol_policy = "redirect-to-https"

    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    compress         = true

    # Cache policy: use AWS managed "CachingOptimized"
    cache_policy_id = data.aws_cloudfront_cache_policy.caching_optimized.id

    # We don't need to forward cookies/querystrings for a pure static SPA,
    # so we can also attach an origin request policy of "AllViewerExceptHostHeader"
    # or leave it empty. We'll leave it empty for now for simplicity.
  }

  price_class = "PriceClass_100" # cheapest / US+EU mostly. You can bump later.

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
    # If/when you want a custom domain + ACM cert in us-east-1,
    # you'll replace this block.
  }

  tags = {
    Name = "genonaut-${var.env}-static-site-cf"
    Env  = var.env
  }
}

########################################
# Bucket policy allowing CloudFront OAC
########################################

data "aws_iam_policy_document" "static_site_bucket_policy" {
  statement {
    sid = "AllowCloudFrontServicePrincipalReadOnly"

    actions = [
      "s3:GetObject",
    ]

    resources = [
      "${aws_s3_bucket.static_site.arn}/*",
    ]

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.static_site.arn]
    }
  }
}

resource "aws_s3_bucket_policy" "static_site" {
  bucket = aws_s3_bucket.static_site.id
  policy = data.aws_iam_policy_document.static_site_bucket_policy.json
}

########################################
# Data sources for CloudFront managed policies
########################################

data "aws_cloudfront_cache_policy" "caching_optimized" {
  name = "Managed-CachingOptimized"
}
