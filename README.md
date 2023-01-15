# AzureCloudComputing

 Worker:
 
  
sudo vim /usr/lib/systemd/system/worker.service

[Unit]

Description=python worker

[Install]

WantedBy=multi-user.target

[Service]

User=root

WorkingDirectory=/opt/AzureCloudComputing/worker

ExecStart= sudo python3 worker.py

Restart=always


 Webapp
  
sudo vim /usr/lib/systemd/system/worker.service

[Unit]

Description=python worker

[Install]

WantedBy=multi-user.target

[Service]

User=root

WorkingDirectory=/opt/AzureCloudComputing/worker

ExecStart= sudo python3 worker.py

Restart=always


 Niste comenzi:
  
sudo systemctl daemon-reload

sudo systemctl enable webapp

sudo systemctl start webapp 
