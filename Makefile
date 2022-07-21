include Makefile.vars

.PHONY: run
run: export TARGET_PATH=$(TARGET)
run: export LIBRARY_PATH=$(LIBRARY)
run:
	python crawler.py $(user) $(block_num)

# should do rather this: https://vsupalov.com/docker-shared-permissions/
.PHONY: docker-run
docker-run:
	docker run --rm -it -e TARGET_PATH=$(TARGET) -e LIBRARY_PATH=$(LIBRARY) \
		-v $(HOME)/Workspace/tiktok-dl/cookies.json:/app/cookies.json -v $(TARGET):$(TARGET) -u 1000:1000 \
		$(DOCKER_IMAGE) $(user) $(block_num)

.PHONY: docker-build
docker-build:
	docker build -t $(DOCKER_IMAGE) .

.PHONY: delete-exited
delete-exited:
	 docker ps -q -f status=exited -f ancestor=tiktok-dl | xargs docker rm
	# docker rm $(docker ps -q --filter status=exited --filter ancestor=tiktok-dl)

.PHONY: list-exited
list-exited:
	docker ps -q -f status=exited -f ancestor=tiktok-dl

.PHONY: list-exited-verbose
list-exited-verbose:
	docker ps -f status=exited -f ancestor=tiktok-dl


.PHONY: test
test:
	mkdir -p test_f



