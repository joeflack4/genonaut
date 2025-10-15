// infra/main/locals.tf
locals {
  stack_name = "${var.name_prefix}-${var.env}"
  common_tags = merge(
    {
      Project = var.name_prefix
      Env     = var.env
      Owner   = "genonaut"
    },
    var.tags
  )
}
