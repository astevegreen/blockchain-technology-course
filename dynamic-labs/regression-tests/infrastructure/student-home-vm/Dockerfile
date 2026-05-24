FROM docker:28-dind

RUN apk add --no-cache \
    bash \
    coreutils \
    curl \
    e2fsprogs \
    findutils \
    git \
    grep \
    python3 \
    rsync \
    sed \
    shadow \
    sudo \
    util-linux

RUN mkdir -p /etc/sudoers.d /src /workspace /workspace/dynamic-labs \
    && addgroup -g 1000 student \
    && adduser -D -u 1000 -G student -h /home/student -s /bin/bash student \
    && addgroup student docker \
    && printf 'student ALL=(ALL) NOPASSWD:ALL\n' > /etc/sudoers.d/90-student-nopasswd \
    && chmod 0440 /etc/sudoers.d/90-student-nopasswd \
    && chown -R student:student /home/student /src /workspace

COPY entrypoint.sh /usr/local/bin/student-home-vm-entrypoint.sh
RUN chmod 755 /usr/local/bin/student-home-vm-entrypoint.sh

ENV DOCKER_TLS_CERTDIR=""

WORKDIR /workspace/dynamic-labs
ENTRYPOINT ["bash", "student-home-vm-entrypoint.sh"]
CMD ["tail", "-f", "/dev/null"]
