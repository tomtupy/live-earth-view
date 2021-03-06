from bs4 import BeautifulSoup
import coloredlogs
import configparser
import imageio
from lib.utils import (
    get_current_utc_timestamp,
    get_image_file_list,
    get_image_file_path,
    get_image_list_within_window,
    get_timestamp_from_file_path,
    parse_image_dimension_str,
    verify_image_dir_existence
)
import logging
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.animation as animation
import numpy as np
import os
import requests
from time import sleep
import urllib.request


# Create a logger object.
logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG')

# Load config
CONFIG_FILE = 'config.ini'
config = configparser.ConfigParser()
config.read(CONFIG_FILE)

IMAGE_SIZE = config['common']['ImageSize']
IMAGE_FORMAT = config['common']['ImageFormat']
IMAGE_DATA_LOCATION = config['common']['ImageDataLocation']
PROCESSED_GIF_LOCATION = config['common']['ProcessedGifLocation']
DATA_FILE_LINK_PREFIX = config['downloader']['DataFileLinkPrefix']
LINK_MATCH_STR = DATA_FILE_LINK_PREFIX + IMAGE_SIZE + IMAGE_FORMAT
DELETE_OLD_DATA = config.getboolean('downloader', 'DeleteOldData')
KEEP_MOST_RECENT_IMAGE = config.getboolean(
    'downloader', 'SkipMostRecentImageCleanup'
)
DATA_URL = config['downloader']['DataURL']
POLL_TIME_SEC = config.getint('downloader', 'PollTimeSec')
INITIAL_DOWNLOAD_WINDOW_MINS = config.getint('common', 'DisplayWindowMins')
IMAGE_DIMENSIONS = parse_image_dimension_str(config['common']['ImageSize'])


def get_last_downloaded_image_timestamp():
    image_file_list = get_image_file_list(
        IMAGE_DATA_LOCATION, config['common']['ImageFormat']
    )
    if (len(image_file_list) > 0):
        logger.debug('Found ' + str(len(image_file_list)) + ' images.')
        last_image_file = image_file_list[-1]
        return get_timestamp_from_file_path(last_image_file)
    logger.warning('No images were found!')
    return None


def get_online_file_url_list():
    page = None
    try:
        page = requests.get(DATA_URL).text
    except Exception as err:
        logger.warning('Data query failed: {0}'.format(err))
        return []
    else:
        soup = BeautifulSoup(page, 'html.parser')
        url_list = [
            DATA_URL + node.get('href')
            for node in soup.find_all('a')
            if node.get('href').endswith(LINK_MATCH_STR)
        ]
        logger.debug('Found ' +
                     str(len(url_list)) +
                     ' images availalble for download.')
        return url_list


def get_timestamp_from_file_url(file_url):
    filename = file_url.replace(DATA_URL, '')
    timestamp = filename.replace('_' + LINK_MATCH_STR, '')
    return int(timestamp)


# Check for image dir, create if not found
if not verify_image_dir_existence(IMAGE_DATA_LOCATION):
    logger.error('Image location directory not found!')
    raise FileNotFoundError

# Check for gif dir, create if not found
if not verify_image_dir_existence(PROCESSED_GIF_LOCATION):
    logger.error('Gif location directory not found!')
    raise FileNotFoundError

# Get initial timestamp
last_timestamp = get_current_utc_timestamp(
    INITIAL_DOWNLOAD_WINDOW_MINS
)
latest_downloaded_timestamp = get_last_downloaded_image_timestamp()
if (
    latest_downloaded_timestamp and
    latest_downloaded_timestamp > last_timestamp
):
    last_timestamp = latest_downloaded_timestamp
logger.debug('Initial data timestamp: ' + str(last_timestamp))

# main loop
update_gif = True if latest_downloaded_timestamp is not None else False
while True:
    # check for new data
    for file_url in get_online_file_url_list():
        timestamp = get_timestamp_from_file_url(file_url)
        if timestamp <= last_timestamp:
            continue

        last_timestamp = timestamp
        logger.info('Downloading ' + file_url)
        try:
            urllib.request.urlretrieve(
                file_url,
                get_image_file_path(
                    IMAGE_DATA_LOCATION,
                    (str(timestamp) + IMAGE_FORMAT))
            )
            update_gif = True
        except Exception as err:
            logger.warning(
                'Image download failed: {0}'.format(err)
            )

    # cleanup
    if DELETE_OLD_DATA:
        oldest_timestamp = get_current_utc_timestamp(
            INITIAL_DOWNLOAD_WINDOW_MINS
        )
        image_file_list = get_image_file_list(
            IMAGE_DATA_LOCATION, IMAGE_FORMAT
        )
        for image_filename in image_file_list[:-1] if KEEP_MOST_RECENT_IMAGE else image_file_list:
            timestamp = get_timestamp_from_file_path(image_filename)
            if (timestamp >= oldest_timestamp):
                break
            else:
                logger.info('Deleting ' + image_filename)
                os.remove(image_filename)

    # Create a gif
    if update_gif:
        fig = plt.figure(tight_layout={"pad": 0})
        image_file_list = get_image_list_within_window(
            INITIAL_DOWNLOAD_WINDOW_MINS,
            IMAGE_DATA_LOCATION,
            IMAGE_FORMAT
        )
        logger.info('Updating output gif with ' +
                    str(len(image_file_list)) +
                    ' images.')
        frames = []
        for image_file in image_file_list:
            logger.debug('Reading ' + image_file)
            try:
                image_data = imageio.imread(image_file)
                # verify image validity
                assert len(image_data.shape) == 3
                assert image_data.shape[0] == IMAGE_DIMENSIONS[0]
                assert image_data.shape[1] == IMAGE_DIMENSIONS[1]
                assert image_data.shape[2] == 3
                frames.append(image_data)
            except Exception as err:
                logger.warning('unable to read ' +
                               image_file +
                               ', Error: {0}'.format(err))
                break
        if frames:
            imageio.mimsave(
                os.path.normpath(PROCESSED_GIF_LOCATION) +
                '/images.gif',
                frames
            )
            logger.info('Gif Update Succesful with ' +
                        str(len(image_file_list)) +
                        ' images.')
            update_gif = False

    # Sleep
    logger.info('Sleeping for ' + str(POLL_TIME_SEC) + ' seconds')
    sleep(POLL_TIME_SEC)
