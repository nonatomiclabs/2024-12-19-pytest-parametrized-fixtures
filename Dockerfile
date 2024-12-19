FROM python:3.13-slim
RUN apt update
RUN apt install -y bat
WORKDIR /home
COPY requirements-frozen.txt /home
RUN pip install -r requirements-frozen.txt
COPY entrypoint.sh /home
COPY tests/ /home
ENTRYPOINT [ "/home/entrypoint.sh" ]