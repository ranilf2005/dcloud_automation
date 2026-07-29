output "inside_network_object_id" {
  description = "ID of the inside network object."
  value       = fmc_network.inside_net.id
}

output "outside_network_object_id" {
  description = "ID of the outside network object."
  value       = fmc_network.outside_net.id
}

output "access_control_policy_id" {
  description = "ID of the created Access Control Policy."
  value       = fmc_access_control_policy.inside_to_outside.id
}
