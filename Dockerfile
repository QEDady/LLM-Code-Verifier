FROM rockylinux:9.3 

RUN dnf install -y sudo git python3 python3-pip python3-devel java-11-openjdk-devel git-lfs

WORKDIR /LLM-Code-Verifier

COPY requirements.txt .
RUN pip install -r requirements.txt

ARG USER_NAME
ARG USER_ID
ARG GROUP_NAME
ARG GROUP_ID

RUN groupadd -g ${GROUP_ID} ${GROUP_NAME} && \
    useradd -m -g ${GROUP_NAME} -G ${GROUP_NAME} -u ${USER_ID} ${USER_NAME}

RUN echo "${USER_NAME} ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

USER ${USER_NAME}

RUN echo "alias cls=clear" >> ~/.bashrc && \
    echo "PS1='\[\e[36m\][\h] \[\e[32m\]\u\[\e[37m\]:\[\e[34m\]\w \[\e[35m\]$(git rev-parse --abbrev-ref HEAD 2>/dev/null | sed "s/^/(/" | sed "s/$/)/")\[\e[0m\]$ '" >> ~/.bashrc