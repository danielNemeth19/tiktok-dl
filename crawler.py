import re
import os
import json
import logging
import argparse
import sys
from pathlib import Path
from TikTokApi import TikTokApi
from TikTokApi.exceptions import TikTokException


class CrawlerError(Exception):
    pass


class Crawler:
    BLOCK_SIZE = 30

    def __init__(self, user):
        self.logger = self._setup_logger()
        self.user = user
        self.cookies = self.get_cookies_from_file()
        self.api = TikTokApi()
        self.api._get_cookies = self.get_cookies
        self._current_count = 0
        self.target_path = self._create_target_path()
        self.local_library = list()
        self._error_cache = dict()

    @staticmethod
    def _setup_logger():
        logging.basicConfig()
        logger = logging.getLogger("crawler_instance")
        logger.setLevel(logging.DEBUG)
        return logger

    def _get_env(self, env):
        env_value = os.getenv(env, None)
        if not env_value:
            return self._handle_exception(f"{env} env needs to be set")
        return env_value

    def _create_target_path(self):
        target_path = self._get_env("TARGET_PATH")
        target_path = Path(target_path, self.user)
        target_path.mkdir(parents=True, exist_ok=True)
        return target_path

    def _get_base_library(self):
        library_path = self._get_env("LIBRARY_PATH")
        return Path(library_path, self.user)

    @staticmethod
    def get_cookies_from_file():
        with open("cookies.json", "r") as f:
            cookies = json.load(f)

        cookie_key_values = dict()
        for cookie in cookies:
            cookie_key_values[cookie["name"]] = cookie["value"]
        return cookie_key_values

    def get_cookies(self, **kwargs):
        return self.cookies

    def collect_library(self):
        library_home = self._get_base_library()

        if not library_home.exists():
            self.logger.info(f"Folder not exists: {library_home}")
            return

        for fn in library_home.iterdir():
            id_candidate = re.search("[0-9]{19}", fn.name)
            if id_candidate:
                self.local_library.append(id_candidate.group())
            else:
                self.logger.info(f"Skipping: {fn.name}")
        self.logger.info(f"Number of videos in library: {len(self.local_library)}")

    def get_timestamps(self):
        for fn in self.target_path.iterdir():
            video_id = re.search("[0-9]{19}", fn.name)
            if video_id:
                video = self.api.video(id=video_id.group())
                print(video.create_time)

    def collect_videos(self, block_num=1, retry_fails=False):
        target_block = block_num * self.BLOCK_SIZE
        user_obj = self.api.user(username=self.user)

        try:
            for video in user_obj.videos(count=target_block):
                self._current_count += 1
                self._save_video(video)
                self.logger.info(f"Count: {self._current_count} id: {video.id}")
        except KeyError:
            self.logger.error(f"Error for {self._current_count}")

        if retry_fails and self._error_cache:
            self.retry_fails()

        self._dump_errors_to_json()
        self.api.shutdown()

    def _save_video(self, video, from_error_cache=False):
        file_name = f"{video.id}_{self.user}.mp4"
        download_target = Path(self.target_path, file_name)

        if self._check_if_exists(video.id, download_target):
            return
        try:
            video_data = video.bytes()
        except (KeyError, TikTokException)as exc:
            self._store_error(video.id, exc.__str__())
            return
        with open(download_target, "wb") as out_file:
            out_file.write(video_data)
            if from_error_cache:
                self._error_cache.pop(video.id)
            self.logger.info(f"Save successful for {file_name}...")

    def _store_error(self, video_id, exc):
        self.logger.error(f"Fails on {video_id} - error cached")
        self._error_cache[video_id] = exc

    def _check_if_exists(self, video_id, download_target: Path):
        if video_id in self.local_library:
            self.logger.info(f"Already in local library! {video_id}")
            return True

        if download_target.exists():
            self.logger.info(f"Already saved!")
            return True

    def retry_fails(self):
        self.logger.info(f"Retrying failures! {self._error_cache.keys()}")
        current_failures = self._error_cache.copy()
        for key in current_failures:
            video = self.api.video(id=key)
            self._save_video(video, from_error_cache=True)

    def _dump_errors_to_json(self):
        file_name = f"{self.user}_error_log.json"
        full_target = Path(self.target_path, file_name)
        with open(full_target, "w") as outfile:
            json.dump(self._error_cache, outfile)

    def read_and_try_errors(self):
        file_name = f"{self.user}_error_log.json"
        full_target = Path(self.target_path, file_name)
        with open(full_target, "r") as f:
            error_json = json.load(f)

        for key, value in error_json.items():
            video = self.api.video(id=key)
            self._save_video(video)
        self._dump_errors_to_json()
        self.api.shutdown()

    def _handle_exception(self, msg):
        self.logger.error(msg)
        self.api.shutdown()
        sys.exit()


def main(options):
    crawler = Crawler(user=options.user)
    crawler.collect_library()
    crawler.collect_videos(block_num=options.block_num, retry_fails=options.retry_fails)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("user", help="User to be crawled")
    parser.add_argument("block_num", type=int, help="Specify how many block of videos iterated: one block is 30 videos")
    parser.add_argument("--retry-fails", action="store_true", help="If specified, re-tries failures from cache")
    args = parser.parse_args()
    main(args)

