# Access Control Policy with a single rule that ALLOWS traffic from the
# inside zone/network to the outside zone/network.
#
# Rules are managed inline (manage_rules = true) per the CiscoDevNet/fmc
# v2.x provider model.
resource "fmc_access_control_policy" "inside_to_outside" {
  name           = var.acp_name
  description    = "Allow traffic from inside to outside (IaC demo)"
  default_action = "BLOCK"

  default_action_log_connection_end = true
  default_action_send_events_to_fmc = true

  manage_rules = true
  rules = [
    {
      name    = "allow-inside-to-outside"
      action  = "ALLOW"
      enabled = true

      source_zones = [
        { id = fmc_security_zone.inside.id }
      ]
      destination_zones = [
        { id = fmc_security_zone.outside.id }
      ]

      source_network_objects = [
        { id = fmc_network.inside_net.id, type = "Network" }
      ]
      destination_network_objects = [
        { id = fmc_network.outside_net.id, type = "Network" }
      ]

      log_connection_end = true
      send_events_to_fmc = true
    }
  ]
}
