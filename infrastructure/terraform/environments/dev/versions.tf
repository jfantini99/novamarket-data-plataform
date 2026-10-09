terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0, < 7.0"
    }
  }

  # State local (fora do Git, ver .gitignore). Um backend remoto (S3 + lock) fica para quando
  # houver mais de uma pessoa aplicando a infraestrutura.
}
