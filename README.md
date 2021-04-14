# Satellite Network Research

Scripts to automatically run experiments with TCP congestion control over the satellite network.

## Requirements

Python 3 is required for this project.

To install dependencies:

```
pip3 install -r requirements.txt
```

## Usage

The Trial class in the module `trial.py` serves as the template class, a basic trial, and can be extended to create customized trials.

To run or create a trial, you can check [hystart_trial.py](../blob/master/hystart_trial.py) for example and modify the file to fill in your SSH username/password and the protocol for the trial.

Then, run

```
python3 hystart_trial.py
```

It will automatically run the trial and generate the plot.

## Credits

This project adapts and uses components written by Kush Shah. You can find the source code of the original project below:

[https://github.com/kush5683/TCP-over-Satellite](https://github.com/kush5683/TCP-over-Satellite)