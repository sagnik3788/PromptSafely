provider "aws" {
  region = "ap-northeast-3"
}

data "aws_ami" "ubuntu_latest" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  filter {
    name   = "root-device-type"
    values = ["ebs"]
  }
}

data "aws_vpc" "default" {
  default = true
}

resource "aws_security_group" "pipecd_ssh" {
  name        = "pipecd-ssh-access"
  description = "Allow SSH access"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "SSH from your IP"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "pipecd_vm" {
  ami                         = data.aws_ami.ubuntu_latest.id
  instance_type               = "t3.micro"
  key_name                    = "osaka"  
  subnet_id                   = "subnet-00c30a0c908c9f2e1"
  associate_public_ip_address = true
  vpc_security_group_ids      = [aws_security_group.pipecd_ssh.id]

  instance_market_options {
    market_type = "spot"
    spot_options {
      spot_instance_type = "one-time" 
    }
  }


  provisioner "file" {
    source      = "piped-config.yaml"
    destination = "/tmp/piped-config.yaml"

    connection {
      type        = "ssh"
      user        = "ubuntu"
      private_key = file("/home/sangnik/.ssh/osaka.pem")
      host        = self.public_ip
    }
  }

  provisioner "remote-exec" {
    inline = [
      "sudo apt update -y",
      "sudo apt install -y curl unzip ",
      "curl -LO https://github.com/pipe-cd/pipe/releases/download/v0.52.2/piped_v0.52.2_linux_amd64",
      "echo 'ac8f7105836eb11645964a97116f8e5c22f830bf5b2735439feece02986d59dc piped_v0.52.2_linux_amd64' | sha256sum -c -",
      "chmod +x piped_v0.52.2_linux_amd64",
      "sudo mv piped_v0.52.2_linux_amd64 /usr/local/bin/piped"
    ]

    connection {
      type        = "ssh"
      user        = "ubuntu"
      private_key = file("/home/sangnik/.ssh/osaka.pem")
      host        = self.public_ip
    }
  }

  tags = {
    Name = "pipecd-vm"
  }
}
