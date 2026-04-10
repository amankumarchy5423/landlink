variable "project_name"      {}
variable "vpc_id"            {}
variable "private_subnet_id" {}
variable "ecs_sg_id"         {}
variable "target_group_arn"  {}
variable "app_port"          {}
variable "docker_image"      {}
variable "db_host"           {}
variable "db_name"           {}
variable "db_username"       {}
variable "db_password"       { sensitive = true }
variable "cluster_id"        {}
variable "cluster_name"      {}