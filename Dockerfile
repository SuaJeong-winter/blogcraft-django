# pull official base image - 도커는 파이썬이 설치되어 있는 이미지를 기본으로 제공
#FROM python:3.8.0-alpine
FROM python:3.8.0-slim-buster

# set work directory - 프로젝트 작업 폴더를 지정
WORKDIR /usr/src/app

# set environment variables - .pyc 파일은 생성하지 않고 파이썬 로그가 버퍼링 없이 즉각적으로 출력되도록
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

#RUN apk update
#RUN apk add postgresql-dev gcc python3-dev musl-dev zlib-dev jpeg-dev #--(5.2)

# 로컬 컴퓨터의 현재 위치에 있는 파일을 모두 작업 폴더로 복사해서 지금까지 작성한 장고 프로젝트가 도커 이미지에 담기도록
COPY . /usr/src/app/

# install dependencies - requirements.txt에 나열된 라이브러리를 설치
RUN pip install --upgrade pip
RUN pip install -r requirements.txt