server {
    listen 80;
    server_name ramacareerinstitute.com www.ramacareerinstitute.com;
     location / {
        proxy_pass http://0.0.0.0:8001;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
    }
location /auth/ {
        proxy_pass http://0.0.0.0:8001;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
    }
location /edu/ {
        proxy_pass http://0.0.0.0:8001;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
    alias /var/www/ramacareerinstitute/static/;
}

location /media/ {
    alias /var/www/ramacareerinstitute/media/;
}

return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name ramacareerinstitute.com www.ramacareerinstitute.com;

    ssl_certificate /etc/letsencrypt/live/ramacareerinstitute.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ramacareerinstitute.com/privkey.pem;

    location / {
        proxy_pass http://0.0.0.0:8001;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
    }
location /auth/ {
        proxy_pass http://0.0.0.0:8001;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
    }
location /edu/ {
       proxy_pass http://0.0.0.0:8001;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
    }
   
location /static/ {
    alias /var/www/ramacareerinstitute/static/;
}

location /media/ {
    alias /var/www/ramacareerinstitute/media/;
}}

