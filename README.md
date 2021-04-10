# Satellite Network Research

Scripts to automatically run experiments with TCP congestion control over the satellite network.

## Requirements

Python 3 is required for this project.

To install dependencies:

```
pip3 install -r requirements.txt
```

## Usage

First, modify `trial.py` to fill in your SSH user/password and the protocol for the trial.

Then, run

```
python3 trial.py
```

The script will automatically run the trial and generate the plot.

## Credits

This project adapts and uses components written by Kush Shah. You can find the source code of the original project below:

[https://github.com/kush5683/TCP-over-Satellite](https://github.com/kush5683/TCP-over-Satellite)