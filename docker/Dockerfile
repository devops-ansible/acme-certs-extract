FROM python:latest
MAINTAINER macwinnie <dev@macwinnie.me>

ENV WORKDIR="/certs_extract"
ENV ACMEDIR="/acme"
ENV CERTSDIR="/certs"

COPY script/  ${WORKDIR}
COPY install/ /install

WORKDIR ${WORKDIR}

RUN chmod a+x /install/install.sh && \
    /install/install.sh

CMD [ "sleep", "infinity" ]
