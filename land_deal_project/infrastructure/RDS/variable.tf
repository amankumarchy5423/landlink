variable "project_name"       {}
variable "vpc_id"             {}
variable "private_subnet_id"  {}
variable "private_subnet_ids" { type = list(string) }  # NEW
variable "ecs_sg_id"          {}
variable "db_name"            {}
variable "db_username"        {}
variable "db_password"        { sensitive = true }