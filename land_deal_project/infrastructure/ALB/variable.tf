variable "project_name"     {}
variable "app_port"         {}
variable "vpc_id"           {}
variable "public_subnet_id" {}
variable "public_subnet_ids" { type = list(string) }  