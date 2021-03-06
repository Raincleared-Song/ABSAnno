# This file is a template, and might need editing before it works on your project.
FROM python:3.7.0

# Edit with mysql-client, postgresql-client, sqlite3, etc. for your needs.
# Or delete entirely if not needed.
# RUN apt-get update \
#     && apt-get install -y --no-install-recommends \
#         postgresql-client \
#     && rm -rf /var/lib/apt/lists/*

ENV HOME=/opt/app

WORKDIR $HOME

COPY requirements.txt $HOME
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir -r requirements.txt

COPY . $HOME

# For Django
EXPOSE 80
ENV PYTHONUNBUFFERED=true
CMD ["/bin/sh", "./run.sh"]
