
all: build

build:
	docker build -t automatest/base base
	docker build -t automatest/cc cc
	docker build -t automatest/java java
	docker build -t automatest/python2 python2
	docker build -t automatest/python3 python3
	docker build -t automatest/all all


clear:
	docker rmi -f automatest/base
	docker rmi -f automatest/cc
	docker rmi -f automatest/java
	docker rmi -f automatest/python2
	docker rmi -f automatest/python3
	docker rmi -f automatest/all

push:
	docker push automatest/base
	docker push automatest/cc
	docker push automatest/java
	docker push automatest/python2
	docker push automatest/python3
	docker push automatest/all
