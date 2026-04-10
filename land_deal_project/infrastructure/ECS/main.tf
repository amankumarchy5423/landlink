resource "aws_ecs_task_definition" "app" {
  family                   = "${var.project_name}-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"    
  memory                   = "512"    
  execution_role_arn       = aws_iam_role.ecs_exec.arn

  container_definitions = jsonencode([{
    name      = var.project_name
    image     = var.docker_image        
    essential = true
    portMappings = [{
      containerPort = var.app_port
      hostPort      = var.app_port
    }]
    environment = [
  { name = "DB_HOST",     value = var.db_host },      
  { name = "DB_PORT",     value = "5432" },
  { name = "DB_NAME",     value = var.db_name },
  { name = "DB_USER",     value = var.db_username },
  { name = "DB_PASSWORD", value = var.db_password },
  { name = "SECRET_KEY",  value = "landlink_secret" },
  { name = "PORT",        value = "8080" },
  { name = "FLASK_ENV",   value = "production" }       
]
  }])
}

resource "aws_iam_role" "ecs_exec" {
  name = "${var.project_name}-ecs-task-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_exec" {
  role       = aws_iam_role.ecs_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_ecs_service" "app" {
  name            = "${var.project_name}-service"
  cluster         = var.cluster_id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = 2          
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = [var.private_subnet_id]
    security_groups  = [var.ecs_sg_id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = var.target_group_arn
    container_name   = var.project_name
    container_port   = var.app_port
  }
}

output "ecs_service_name" { value = aws_ecs_service.app.name }