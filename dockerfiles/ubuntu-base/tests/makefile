all:
	@echo "------------TESTING JAVA------------"
	javac main.java
	java main

	@echo "------------TESTING PYTHON------------"
	python3 main.py
	ls python.png

	@echo "------------TESTING C------------"
	gcc main.c -o c.out
	./c.out

	@echo "------------TESTING CC------------"
	g++ main.cc -o cc.out
	./cc.out

	@echo "------------TESTING CS------------"
	mcs main.cs -out:cs.out
	mono cs.out

	