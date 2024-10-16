# Utiliza una imagen base oficial de Debian
FROM debian:bullseye-slim

# Actualiza los paquetes e instala dependencias necesarias
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libncurses5-dev \
    libnewt-dev \
    libxml2-dev \
    libsqlite3-dev \
    uuid-dev \
    wget \
    curl \
    libjansson-dev \
    libedit-dev \
    sudo \
    net-tools \
    iputils-ping \
    vim \
    git

# Descarga los archivos fuente de Asterisk 16.29.0
WORKDIR /usr/src
RUN wget https://downloads.asterisk.org/pub/telephony/asterisk/old-releases/asterisk-16.29.0.tar.gz \
    && tar xzf asterisk-16.29.0.tar.gz

# Cambia al directorio de Asterisk
WORKDIR /usr/src/asterisk-16.29.0

# Instala las dependencias adicionales y prepara el entorno
RUN ./contrib/scripts/install_prereq install

# Configura e instala Asterisk
RUN ./configure \
    && make menuselect.makeopts \
    && menuselect/menuselect --enable CORE-SOUNDS-EN-WAV --enable MOH-OPSOUND-WAV --enable app_macro menuselect.makeopts \
    && make \
    && make install \
    && make samples \
    && make config \
    && ldconfig

# Expone los puertos necesarios para SIP y otros servicios
EXPOSE 5060/udp 5060/tcp 5160/udp 5160/tcp 10000-20000/udp

# Establece el comando por defecto al iniciar el contenedor
CMD ["/usr/sbin/asterisk", "-f", "-vvv"]
