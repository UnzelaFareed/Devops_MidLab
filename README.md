# Daily Task Manager (CSC418 Lab Mid)

Flask + PostgreSQL task manager deployed with Docker Compose on AWS EC2,
behind an Application Load Balancer and Auto Scaling Group.

## Architecture
User -> ALB -> 2 EC2 instances (ASG) -> Docker Compose (Flask web + PostgreSQL + named volume)

## Run locally / on EC2
    cp .env.example .env
    docker compose up -d --build
    curl http://localhost/health

## Features
Add, edit, delete, complete tasks; priority; due date; search; /api/tasks (JSON); /health.

## Test
    pip install selenium
    python test_selenium.py http://<URL>