FROM centos:7

#enable systemd
ENV container docker
VOLUME [ "/sys/fs/cgroup" ]

ADD scylla_bashrc /scylla_bashrc

# Scylla configuration:
ADD etc/sysconfig/scylla-server /etc/sysconfig/scylla-server

# Supervisord configuration:
ADD etc/supervisord.conf /etc/supervisord.conf
ADD etc/supervisord.conf.d/scylla-server.conf /etc/supervisord.conf.d/scylla-server.conf
ADD etc/supervisord.conf.d/scylla-jmx.conf /etc/supervisord.conf.d/scylla-jmx.conf
ADD scylla-service.sh /scylla-service.sh
ADD scylla-jmx-service.sh /scylla-jmx-service.sh

# Install Scylla:
RUN curl http://downloads.scylladb.com.s3.amazonaws.com/rpm/centos/scylla-2.0.repo -o /etc/yum.repos.d/scylla.repo && \
    yum -y install epel-release && \
    yum -y clean expire-cache && \
    yum -y update && \
    yum -y remove boost-thread boost-system && \
    yum -y install scylla hostname supervisor jq && \
    yum clean all && \
    yum -y install python34 python34-PyYAML && \
    cat /scylla_bashrc >> /etc/bashrc && \
    mkdir -p /etc/supervisor.conf.d && \
    mkdir -p /var/log/scylla/{data,commitlog} && \
    chown -R scylla.scylla /var/lib/scylla/{data,commitlog} && \
    mkdir -p /etc/scylla/keys/{client,node} && \
    chmod 644 -R /etc/scylla/keys

# Docker image startup scripts:
ADD scyllasetup.py /scyllasetup.py
ADD environmentcollector.py /environmentcollector.py
ADD docker-entrypoint.py /docker-entrypoint.py
ADD system_auth_replicator.sh /system_auth_replicator.sh
RUN chmod a+x /system_auth_replicator.sh

ENTRYPOINT ["/docker-entrypoint.py"]

EXPOSE 10000 9042 9160 9180 7000 7001
VOLUME [ "/var/lib/scylla" ]
