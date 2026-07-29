# Security zones for the inside and outside interfaces.
resource "fmc_security_zone" "inside" {
  name           = "inside-zone"
  interface_type = "ROUTED"
}

resource "fmc_security_zone" "outside" {
  name           = "outside-zone"
  interface_type = "ROUTED"
}
