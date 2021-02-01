from datetime import datetime, timedelta
import glob
import os


def compute_list_diff(list1, list2):
    return [element for element in list1 if element not in list2]


def get_timestamp_from_file_path(file_path):
    return int(os.path.splitext(os.path.basename(file_path))[0])


def get_image_file_list(data_path, image_format):
    return sorted(
        glob.glob(os.path.normpath(data_path) + '/*' + image_format)
    )


def get_image_file_path(path, filename):
    return os.path.abspath(path) + '/' + filename


def get_current_utc_timestamp(preceeding_minutes=0):
    # Timestamp format:
    # 4 digit year
    # 3 digit day of year
    # 2 digit hour
    # 2 digit minute
    # 2 digit second - <discard>
    # 1 digit tenth of second - <discard>
    dt_now = datetime.utcnow() - timedelta(minutes=preceeding_minutes)
    return int(dt_now.strftime('%Y%j%H%M'))


def get_image_list_within_window(display_window_mins, image_location, image_format):
    oldest_allowable_timestamp = get_current_utc_timestamp(display_window_mins)
    return [
        image_file for image_file in
        get_image_file_list(image_location, image_format)
        if get_timestamp_from_file_path(image_file) >=
        oldest_allowable_timestamp
    ]


def parse_image_dimension_str(dim_str):
    return [int(dim) for dim in dim_str.split('x')]


def verify_image_dir_existence(dir_path):
    if not os.path.exists(dir_path):
        os.mkdir(dir_path)
    return os.path.exists(dir_path)
