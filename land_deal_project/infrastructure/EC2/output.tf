output "ecs_sg_id"        { value = aws_security_group.ecs_sg.id }
output "ecs_exec_role_arn"{ value = aws_iam_role.ecs_exec.arn }
output "ecs_cluster_id"   { value = aws_ecs_cluster.main.id }
output "ecs_cluster_name" { value = aws_ecs_cluster.main.name }