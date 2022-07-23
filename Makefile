TARGET=${HOME}/Downloads/tiktok
LIBRARY = /media/${USER}/data/vmimages/sysm/tiktok/
COOKIES_PATH=${HOME}/Workspace/tiktok-dl
COOKIES_FILE=cookies.json
DOCKER_IMAGE = tiktok-dl
USER_ID = $(shell id -u)
GROUP_ID = $(shell id -g)

.PHONY: run
run: export TARGET_PATH=$(TARGET)
run: export LIBRARY_PATH=$(LIBRARY)
run:
	python crawler.py $(user) $(block_num)

.PHONY: docker-build
docker-build:
	docker build -t $(DOCKER_IMAGE) .

.PHONY: docker-run
docker-run:
	docker run --rm -it -e TARGET_PATH=$(TARGET) -e LIBRARY_PATH=$(LIBRARY) \
		-v $(COOKIES_PATH)/$(COOKIES_FILE):/app/$(COOKIES_FILE) -v $(TARGET):$(TARGET) \
		$(DOCKER_IMAGE) $(user) $(block_num)

.PHONY: delete-exited
delete-exited:
	 docker rm $(shell docker ps -q --filter status=exited)

.PHONY: list-exited
list-exited:
	ids = docker ps -q -f status=exited -f ancestor=tiktok-dl
	echo $(ids)

.PHONY: list-exited-verbose
list-exited-verbose:
	docker ps -f status=exited -f ancestor=tiktok-dl


