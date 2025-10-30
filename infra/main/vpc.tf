#################################
# VPC / Subnets / Routing / NAT
#################################
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "genonaut-vpc"
    Env  = var.env
  }
}

# Internet Gateway for public subnet egress
resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "genonaut-igw"
    Env  = var.env
  }
}

# todo: later can do: "availability_zone = "${var.region}a"" for more custom deployment / redundancy
# Public subnet (for ALB, NAT gateway, etc.)
resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = true
  availability_zone       = "us-east-1a"

  tags = {
    Name = "genonaut-public-subnet-a"
    Tier = "public"
    Env  = var.env
  }
}

# Second public subnet in a different AZ (needed for ALB)
resource "aws_subnet" "public_b" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.4.0/24"
  map_public_ip_on_launch = true
  availability_zone       = "us-east-1b"

  tags = {
    Name = "genonaut-public-subnet-b"
    Tier = "public"
    Env  = var.env
  }
}

# Private subnet (for ECS tasks, DB, Redis, etc.)
resource "aws_subnet" "private" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.2.0/24"
  map_public_ip_on_launch = false
  availability_zone       = "us-east-1a" # match above AZ

  tags = {
    Name = "genonaut-private-subnet-a"
    Tier = "private"
    Env  = var.env
  }
}

# Second private subnet in a different AZ (for RDS requirement)
resource "aws_subnet" "private_b" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.3.0/24"        # different /24
  map_public_ip_on_launch = false
  availability_zone       = "us-east-1b"        # different AZ

  tags = {
    Name = "genonaut-private-subnet-b"
    Tier = "private"
    Env  = var.env
  }
}

# Public route table (internet-bound)
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }

  tags = {
    Name = "genonaut-public-rt"
    Env  = var.env
  }
}

# Associate public subnet with public route table
resource "aws_route_table_association" "public_assoc" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "public_b_assoc" {
  subnet_id      = aws_subnet.public_b.id
  route_table_id = aws_route_table.public.id
}

# Elastic IP for NAT Gateway (so private subnet can get outbound internet)
resource "aws_eip" "nat" {
  domain = "vpc"

  tags = {
    Name = "genonaut-nat-eip"
    Env  = var.env
  }
}

# NAT Gateway lives in the public subnet
resource "aws_nat_gateway" "this" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public.id

  tags = {
    Name = "genonaut-nat"
    Env  = var.env
  }

  depends_on = [aws_internet_gateway.igw]
}

# Private route table (routes 0.0.0.0/0 to NAT, not IGW)
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.this.id
  }

  tags = {
    Name = "genonaut-private-rt"
    Env  = var.env
  }
}

# Associate private subnet with private route table
resource "aws_route_table_association" "private_assoc" {
  subnet_id      = aws_subnet.private.id
  route_table_id = aws_route_table.private.id
}

resource "aws_route_table_association" "private_b_assoc" {
  subnet_id      = aws_subnet.private_b.id
  route_table_id = aws_route_table.private.id
}
