# Run from videobay_gui/ or via `make -C videobay_gui <target>`. The root Makefile belongs to upstream yt-dlp.
VIDEOBAY_REPOSITORY_ROOT := $(abspath ..)
VIDEOBAY_GIT_SHA := $(shell git rev-parse --short=12 HEAD)
VIDEOBAY_BUILDER_IMAGE := localhost/videobay-gui-builder:latest
VIDEOBAY_BUILT_BINARY := dist/$(VIDEOBAY_GIT_SHA)/videobay-gui
# PROVENANCE: ADR-0008. Bump version and checksum together; the checksum comes from the
# release asset deno-x86_64-unknown-linux-gnu.zip.sha256sum.
VIDEOBAY_PINNED_DENO_VERSION := 2.9.8
VIDEOBAY_PINNED_DENO_ZIP_SHA256 := e890975bc2549807bbcc0b584ffafda72cc7c93349dd99c80483dd784f6c4609
VIDEOBAY_PINNED_DENO_EXECUTABLE := build/deno-$(VIDEOBAY_PINNED_DENO_VERSION)/deno
# WHY: $$PWD in container commands is /workspace/videobay_gui; PyInstaller resolves relative
# --add-binary paths against --specpath (/tmp), so they must be absolute.
# WHY: keep-id + --user maps the host user into the rootless container so files written to dist/
# stay owned by you (the image default USER 10001 would map to a subuid instead).
VIDEOBAY_PODMAN_RUN := podman run --rm --userns=keep-id --user $(shell id -u):$(shell id -g) \
	-v $(VIDEOBAY_REPOSITORY_ROOT):/workspace:Z -w /workspace/videobay_gui $(VIDEOBAY_BUILDER_IMAGE)

.PHONY: test lint ci test-ui test-integration builder-image binary install rollback run

test:
	uv run pytest -m "not ui and not integration" --cov --cov-report=term-missing

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run pyright
	./scripts/check_file_length.sh

ci: lint test
	@echo "CI OK ($(VIDEOBAY_GIT_SHA))"

run:
	uv run videobay-gui

test-integration:
	uv run pytest -m integration

builder-image:
	podman build -t $(VIDEOBAY_BUILDER_IMAGE) -f Containerfile --ignorefile .containerignore .

test-ui: builder-image
	$(VIDEOBAY_PODMAN_RUN) sh -c 'uv sync --frozen && xvfb-run -a uv run pytest -m ui'

$(VIDEOBAY_PINNED_DENO_EXECUTABLE):
	./scripts/fetch_pinned_deno_executable.sh $(VIDEOBAY_PINNED_DENO_VERSION) \
		$(VIDEOBAY_PINNED_DENO_ZIP_SHA256) $(dir $(VIDEOBAY_PINNED_DENO_EXECUTABLE))

binary: builder-image $(VIDEOBAY_PINNED_DENO_EXECUTABLE)
	$(VIDEOBAY_PODMAN_RUN) sh -c 'uv sync --frozen && uv run pyinstaller --noconfirm --onefile \
		--name videobay-gui --collect-data customtkinter \
		--add-binary $$PWD/$(VIDEOBAY_PINNED_DENO_EXECUTABLE):. \
		--distpath dist/$(VIDEOBAY_GIT_SHA) --workpath /tmp/videobay-pyinstaller-build --specpath /tmp \
		src/videobay_gui/__main__.py'
	@echo "Built $(VIDEOBAY_BUILT_BINARY)"

install:
	./deploy/install_videobay_gui_binary_by_git_sha.sh $(VIDEOBAY_GIT_SHA) $(VIDEOBAY_BUILT_BINARY)

rollback:
	./deploy/rollback_videobay_gui_to_previous_git_sha.sh
