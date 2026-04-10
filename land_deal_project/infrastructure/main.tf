module "vpc" {
  source       = "./vpc"
  project_name = var.project_name
  aws_region   = var.aws_region
}

module "alb" {
  source           = "./ALB"
  project_name     = var.project_name
  app_port         = var.app_port
  vpc_id           = module.vpc.vpc_id
  public_subnet_id = module.vpc.public_subnet_id
  public_subnet_ids = module.vpc.public_subnet_ids   # NEW
}

module "ec2" {
  source            = "./EC2"
  project_name      = var.project_name
  vpc_id            = module.vpc.vpc_id
  private_subnet_id = module.vpc.private_subnet_id
  alb_sg_id         = module.alb.alb_sg_id
}

module "rds" {
  source             = "./RDS"
  project_name       = var.project_name
  vpc_id             = module.vpc.vpc_id
  private_subnet_id  = module.vpc.private_subnet_id
  private_subnet_ids = module.vpc.private_subnet_ids  # NEW
  ecs_sg_id          = module.ec2.ecs_sg_id
  db_name            = var.db_name
  db_username        = var.db_username
  db_password        = var.db_password
}

module "ecs" {
  source            = "./ECS"
  project_name      = var.project_name
  vpc_id            = module.vpc.vpc_id
  private_subnet_id = module.vpc.private_subnet_id
  ecs_sg_id         = module.ec2.ecs_sg_id
  target_group_arn  = module.alb.target_group_arn
  app_port          = var.app_port
  docker_image      = var.docker_image
  db_host           = module.rds.db_endpoint
  db_name           = var.db_name
  db_username       = var.db_username
  db_password       = var.db_password
  cluster_id        = module.ec2.ecs_cluster_id
  cluster_name      = module.ec2.ecs_cluster_name
}

module "asg" {
  source           = "./ASG"
  project_name     = var.project_name
  ecs_cluster_name = module.ec2.ecs_cluster_name
  ecs_service_name = module.ecs.ecs_service_name
}