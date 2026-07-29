terraform {
  required_version = ">= 1.0"

  required_providers {
    fmc = {
      source  = "CiscoDevNet/fmc"
      version = "~> 2.5"
    }
  }
}
