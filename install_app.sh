#!/bin/bash


set -a
. settings.ini
set +a

. $venv_dir/bin/activate


echo "Stopping application..."
sudo systemctl stop cleaning-app.service

echo "Launching application..."
export BASE_DIR=$(readlink -e "${0%/*}")
envsubst '${USER} ${BASE_DIR} ${gun_num_workers} ${gun_port} ${venv_dir}' < cleaning-app.service | sudo tee /etc/systemd/system/cleaning-app.service || exit 1
sudo systemctl daemon-reload || exit 1
sudo systemctl enable cleaning-app || exit 1
sudo systemctl start cleaning-app || exit 1

