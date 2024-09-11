FROM rockylinux:9.3 

RUN dnf install -y sudo git python3 python3-pip python3-devel

WORKDIR /LLM-Code-Verifier
RUN pip install -r requirements.txt

# Create a group and user
ARG USER_NAME
ARG USER_ID
ARG GROUP_NAME
ARG GROUP_ID
RUN groupadd -g ${GROUP_ID} ${GROUP_NAME} && useradd ${USER_NAME} -G ${GROUP_NAME}
RUN usermod -u ${USER_ID} ${USER_NAME}

RUN echo "${USER_NAME} ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

USER ${USER_NAME}