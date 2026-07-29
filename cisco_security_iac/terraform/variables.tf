variable "fmc_url" {
  description = "Base URL of the FMC instance, e.g. https://198.18.1.10 (Pair A) or https://198.18.1.11 (Pair B)."
  type        = string
  default     = "https://198.18.1.10"
}

variable "fmc_username" {
  description = "FMC administrative username."
  type        = string
  default     = "admin"
}

variable "fmc_password" {
  description = "FMC administrative password. Set via TF_VAR_fmc_password or FMC_PASSWORD; do not commit."
  type        = string
  sensitive   = true
}

variable "fmc_insecure" {
  description = "Skip TLS certificate verification (lab FMC uses a self-signed certificate)."
  type        = bool
  default     = true
}

variable "inside_network_cidr" {
  description = "Inside subnet in CIDR notation (dCloud FTD interface4 / inside side)."
  type        = string
  default     = "198.18.2.0/24"
}

variable "outside_network_cidr" {
  description = "Outside subnet in CIDR notation (dCloud FTD interface1 / outside side)."
  type        = string
  default     = "198.18.1.0/24"
}

variable "acp_name" {
  description = "Name of the Access Control Policy to create."
  type        = string
  default     = "inside-to-outside-policy"
}
