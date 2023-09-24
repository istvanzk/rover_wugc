#!/bin/bash

# Install, activate and check the '4tronix M.A.R.S. Rover Robot' services

echo "Copy service units..."
sudo cp -v driverover.service /lib/systemd/system/driverover.service
sudo cp -v cleansd.service /lib/systemd/system/cleansd.service
sudo cp -v battsd.service /lib/systemd/system/battsd.service

echo "Enable services..."
sudo systemctl enable driverover
sudo systemctl enable cleansd
sudo systemctl enable battsd

echo "Reload systemd daemon..."
sudo systemctl daemon-reload

echo "Start services..."
sudo systemctl start driverover
sudo systemctl start cleansd
sudo systemctl start battsd

echo "Check status..."
systemctl status driverover
systemctl status cleansd
systemctl status battsd