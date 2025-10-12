FROM postgis/postgis:17-3.5

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
         build-essential \
         postgresql-server-dev-17 \
         git \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --branch v0.8.1 https://github.com/pgvector/pgvector.git /tmp/pgvector \
    && cd /tmp/pgvector \
    && make PG_CONFIG=/usr/lib/postgresql/17/bin/pg_config \
    && make install PG_CONFIG=/usr/lib/postgresql/17/bin/pg_config

RUN mkdir -p /usr/share/postgresql/17/extension/ \
    && mkdir -p /usr/lib/postgresql/17/lib/ \
    && cp /usr/share/postgresql/*/extension/vector* /usr/share/postgresql/17/extension/ 2>/dev/null || true \
    && cp /usr/lib/postgresql/*/lib/vector.so /usr/lib/postgresql/17/lib/ 2>/dev/null || true

RUN apt-get remove -y build-essential git \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

COPY backend_helper_course/init-postgis.sh /docker-entrypoint-initdb.d/