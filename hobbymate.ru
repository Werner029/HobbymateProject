upstream keycloak {
    server keycloak:8080;
    keepalive 32;
}

upstream backend_app {
    server backend:8000;    
    keepalive 32;
}

limit_req_zone $binary_remote_addr zone=mylimit:10m rate=5r/s;
limit_conn_zone $binary_remote_addr zone=connlimit:10m;

server {
    listen 80;
    server_name hobbymate.ru www.hobbymate.ru;
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name hobbymate.ru www.hobbymate.ru;
    index index.html;
    ssl_certificate /etc/nginx/ssl/hobbymate.ru/cert.crt;
    ssl_certificate_key /etc/nginx/ssl/hobbymate.ru/cert.key;
    ssl_trusted_certificate /etc/nginx/ssl/hobbymate.ru/ca.crt;
    ssl_protocols TLSv1.3;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    ssl_stapling on;
    ssl_stapling_verify on;
    resolver 77.88.8.8 8.8.8.8 valid=300s;
    resolver_timeout 5s;

    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options SAMEORIGIN;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "no-referrer-when-downgrade";
    add_header Permissions-Policy "geolocation=(), microphone=()";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header Content-Security-Policy "frame-ancestors 'self';" always;

    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    large_client_header_buffers 4 16k;
    proxy_buffer_size 32k;
    proxy_buffers 8 32k;
    proxy_busy_buffers_size 64k;

    location ~ /\.(?!well-known).* {
        deny all;
    }

    root /var/www/hobbymate/static;
    index index.html;
    location / {
    try_files $uri $uri/ /index.html;
    }
    location /api/ {

        limit_req   zone=mylimit  burst=10 nodelay;
        limit_conn  connlimit 10;

        proxy_pass         http://backend_app;
        proxy_set_header   Host              $host;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade $http_upgrade;
        proxy_set_header   Connection "upgrade";
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Host  $host;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }

    location /admin/ {
        proxy_pass         http://backend_app;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
    }

    location /ws/ {
        proxy_pass         http://backend_app;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade           $http_upgrade;
        proxy_set_header   Connection        "Upgrade";
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
    }

    location /keycloak/ {
    proxy_pass         http://keycloak;
    proxy_http_version 1.1;
    proxy_set_header   Host              $http_host;
    proxy_set_header   X-Real-IP         $remote_addr;
    proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
    proxy_set_header   X-Forwarded-Proto $scheme;
    proxy_set_header   X-Forwarded-Host  $http_host;
    proxy_set_header   X-Forwarded-Port  $server_port;
    proxy_set_header   Connection        "";
    }

    location /swagger/ { return 404; }
    location /redoc/   { return 404; }

    access_log /var/log/nginx/hobbymate.access.log;
    error_log  /var/log/nginx/hobbymate.error.log warn;
    server_tokens off;
    autoindex off;
} 