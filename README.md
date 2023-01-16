## AzureCloudComputing

Scripts for our cloud computing class using Microsoft Azure cloud platform.

The user can upload an ``*.wav`` and select an input language and receive the corresponding speech-to-text result of their audio file through email.

The webapp adds the new job to the job queue where worker VMs periodically process jobs from the queue.


Azure services used:

    - Load balancer
    - Webapp scaleset
    - job Queue
    - Blob Storage
    - Worker scaleset
    - Azure Speech Service
    - Email service



### Webapp service
  
```
sudo vim /usr/lib/systemd/system/webapp.service

    [Unit]
    Description=flask webapp
    [Install]
    WantedBy=multi-user.target
    [Service]
    User=root
    WorkingDirectory=/opt/AzureCloudComputing/webserver
    ExecStart=sudo python3 worker.py
    Restart=always

sudo systemctl daemon-reload

sudo systemctl enable webapp

sudo systemctl start webapp
```




### Worker service:
 
```
sudo vim /usr/lib/systemd/system/worker.service

    [Unit]
    Description=python worker
    [Install]
    WantedBy=multi-user.target
    [Service]
    User=root
    WorkingDirectory=/opt/AzureCloudComputing/worker
    ExecStart=sudo python3 worker.py
    Restart=always

sudo systemctl daemon-reload

sudo systemctl enable worker

sudo systemctl start worker
```
