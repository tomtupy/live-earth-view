import coloredlogs
import configparser
from lib.utils import (
    compute_list_diff,
    get_current_utc_timestamp,
    get_image_file_list,
    get_timestamp_from_file_path,
    parse_image_dimension_str,
    verify_image_dir_existence
)
import logging
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.animation as animation
import numpy as np

# Create a logger object.
logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG')

CONFIG_FILE = 'config.ini'
config = configparser.ConfigParser()
config.read(CONFIG_FILE)

IMAGE_FORMAT = config['common']['ImageFormat']
IMAGE_DATA_LOCATION = config['common']['ImageDataLocation']
DISPLAY_WINDOW_MINS = config.getint('common', 'DisplayWindowMins')
FRAME_INTERVAL_MSEC = config.getint('display', 'FrameIntervalMsec')
IMAGE_DIMENSIONS = parse_image_dimension_str(config['common']['ImageSize'])


def get_image_list_within_window():
    oldest_allowable_timestamp = get_current_utc_timestamp(DISPLAY_WINDOW_MINS)
    return [
        image_file for image_file in
        get_image_file_list(IMAGE_DATA_LOCATION, IMAGE_FORMAT)
        if get_timestamp_from_file_path(image_file) >=
        oldest_allowable_timestamp
    ]

# Check for image dir
if not verify_image_dir_existence(IMAGE_DATA_LOCATION):
    logger.error('Image location directory not found!')
    raise FileNotFoundError

# Set up plot
fig = plt.figure(tight_layout={"pad": 0})
plt.axis('off')
fig.patch.set_facecolor('xkcd:grey')

# global image store
image_file_list = []
image_data_list = []
im = plt.imshow(
    np.zeros((IMAGE_DIMENSIONS[0], IMAGE_DIMENSIONS[1], 3), np.uint8),
    animated=True
)


def update_image_data():
    global image_file_list
    global image_data_list

    new_image_file_list = get_image_list_within_window()

    # prune old images
    old_image_files = compute_list_diff(
        image_file_list, new_image_file_list
    )
    while old_image_files:
        logger.debug('Unloading old image ' + old_image_files[0])
        old_image_idx = image_file_list.index(old_image_files[0])
        del image_file_list[old_image_idx]
        del image_data_list[old_image_idx]
        old_image_files = compute_list_diff(
            image_file_list, new_image_file_list
        )

    # append new images
    new_image_files = compute_list_diff(
        new_image_file_list, image_file_list
    )
    if new_image_files:
        logger.debug(str(len(new_image_files)) + ' new images were found!')
        for image_file in new_image_files:
            logger.debug('Reading ' + image_file)
            try:
                image_data = mpimg.imread(image_file)
                # verify image validity
                assert len(image_data.shape) == 3
                assert image_data.shape[0] == IMAGE_DIMENSIONS[0]
                assert image_data.shape[1] == IMAGE_DIMENSIONS[1]
                assert image_data.shape[2] == 3
            except:
                logger.warning('unable to read ' + image_file)
                break
            image_data_list.append(image_data)
            image_file_list.append(image_file)


def render_init():
    # Initial data load
    update_image_data()
    if not image_data_list:
        logger.error('No images were found!')
        exit(0)
    logger.info('Found ' +
                str(len(image_file_list)) +
                ' images on initial load.')
    return [im]


def get_frame(i):
    global im
    frame_idx = int(i % len(image_data_list))
    # refresh data
    if frame_idx == 0:
        logger.debug(
                    'Checking for new imagery... Current image count: ' +
                    str(len(image_file_list)))
        update_image_data()
    im.set_data(image_data_list[frame_idx])
    return [im]


ani = animation.FuncAnimation(
    fig,
    get_frame,
    init_func=render_init,
    interval=FRAME_INTERVAL_MSEC,
    blit=False,
    repeat_delay=0
)

plt.show()
