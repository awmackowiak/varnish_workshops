FROM debian:bookworm-slim AS build
ARG VARNISH_VERSION=6.0.18
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates curl build-essential pkg-config python3 python3-docutils \
      python3-sphinx libpcre2-dev libpcre3-dev libedit-dev libncurses-dev \
      automake autoconf libtool \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /src
RUN curl -fsSL -o varnish.tgz https://varnish-cache.org/downloads/varnish-${VARNISH_VERSION}.tgz \
 && tar xzf varnish.tgz --strip-components=1 \
 && ./configure --prefix=/usr/local \
 && make -j"$(nproc)" && make install DESTDIR=/out

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
      libpcre3 libedit2 libncurses6 libgcc-s1 gcc libc6-dev curl procps \
 && rm -rf /var/lib/apt/lists/* \
 && useradd -r varnish
COPY --from=build /out/usr/local /usr/local
RUN ldconfig
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
EXPOSE 6081 6082
ENTRYPOINT ["/entrypoint.sh"]
