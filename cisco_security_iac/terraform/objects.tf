# Network objects representing the inside and outside subnets.
resource "fmc_network" "inside_net" {
  name        = "inside-net"
  description = "Inside subnet (IaC demo)"
  prefix      = var.inside_network_cidr
}

resource "fmc_network" "outside_net" {
  name        = "outside-net"
  description = "Outside subnet (IaC demo)"
  prefix      = var.outside_network_cidr
}
