# variable "aws_region" {
#   default = "us-east-1"      
# }

# variable "project_name" {
#   default = "landlink"
# }

# variable "app_port" {
#   default = 8080             
# }

# variable "docker_image" {
#   default = "amanmlops/landlink:v2"  
# }

# variable "db_name" {
#   default = "landlink_db"
# }

# variable "db_username" {
#   default = "landlink_user"
# }

# variable "db_password" {
#   default   = "Aman5423"  
#   sensitive = true
# }

variable "aws_region" {
  default = "us-east-1"
}

variable "project_name" {
  default = "landlink"
}

variable "app_port" {
  default = 8080                             
}

variable "docker_image" {
  default = "amanmlops/landlink:v2"           
}

variable "db_name" {
  default = "landlink_db"                     
}

variable "db_username" {
  default = "landlink_user"                   
}

variable "db_password" {
  default   = "Aman5423"                      
  sensitive = true
}