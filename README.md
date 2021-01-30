## About The Project

The project was created to display an animated live view of the earth, from a either GEOS-16 or GEOS-17 satellite imagery. Originally desgined to run on SBCs like rasberryPi or librePC, no web browser is needed and it can be configured to use very minimal CPU and memory resources.

![Project screenshot](/screen.png?raw=true)


## Getting Started

### Prerequisites

1. Install pip3 and dependencies for matplotlib
   ```sh
   apt-get install python3-pip python3-setuptools libjpeg62-turbo-dev zlib1g-dev
   ```
2. Install python packages
   ```sh
    pip3 install cython
    pip3 install -r requirements.txt
    ```

## Usage

This project consists of two scripts that run in parallel, one is used to manage satellite imagery data and the other to render it.

### `downloader.py`

```sh
python3 downloader.py
```

### `display.py`

This script should be started only after the downloader script has started pulling down imagery.
```sh
python3 display.py
```
