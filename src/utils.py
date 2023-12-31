""" Utility scripts"""
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler


def prepare_data(data_path: str, col1, col2, d_format="%Y%m") -> pd.DataFrame:
    """Reads the raw data, extracts essential columns and scales them.

    Args:
        data_path: path to the .csv file with raw data
        col1: column with timestamps
        col2: column with values (to be aggregated by col1)
        d_format: timestamp format, default "%Y%m" (e.g.: 202306)

    Returns:
        pandas dataframe with two columns and scaled values

    """
    try:
        data = pd.read_csv(data_path)
    except FileNotFoundError as exc:
        print("File not found!")
        raise FileNotFoundError from exc

    data[col1] = pd.to_datetime(data[col1].astype(str), format=d_format)

    df_subset = data[[col1, col2]]
    df_subset = df_subset.groupby(col1).sum()
    df_subset.sort_values(by=col1, inplace=True)

    scaler = MinMaxScaler()
    df_subset[col2] = scaler.fit_transform(df_subset)
    return df_subset


def _split_sequence(sequence, n_input: int, n_output: int) -> np.array:
    """Splits a times series sequence into input and output sequences of given lengths
    [1,2,3,4,5] for (seq, 3, 2) gives --> [[1,2,3], [2,3,4]] and [[3,4], [4,5]]

    Args:
        sequence: a time series to be split
        n_input: number of input steps
        n_output: number of output steps

    Returns:
        two numpy arrays (inputs and outputs)

    """
    try:
        if len(sequence) < n_input + n_output:
            print("sequence to short")
            sys.exit()
    except ValueError:
        sys.exit("sequence too short - aborting operation")

    inputs, outputs = [], []
    for i, _ in enumerate(sequence):
        input_end = i + n_input
        output_end = input_end + n_output - 1
        # stop if we reach end of the sequence
        if output_end > len(sequence):
            break

        seq_x, seq_y = sequence[i:input_end], sequence[input_end - 1 : output_end]
        inputs.append(seq_x)
        outputs.append(seq_y)
    return np.array(inputs), np.array(outputs)


def plot_validation(model, val_set, y_test, i):
    """Plot a line graph showing inputs and forecast vs. expected values

    Args:
        model: keras model object
        val_set: validation set
        y_test: expected values
        i: number of input set

    Returns: matplotlib axes

    """

    if i > len(y_test):
        raise IndexError

    forecasts = model.predict(val_set, verbose=0)

    x_pred = forecasts[i].flatten()
    x_pred_len = len(val_set[i])

    model_output = pd.DataFrame(
        {"date": np.arange(x_pred_len, x_pred_len + len(x_pred)) - 1, "output": x_pred}
    ).set_index("date", drop=True)

    model_input = pd.DataFrame(
        {"date": range(x_pred_len), "input": val_set[i].flatten()}
    ).set_index("date", drop=True)

    expected = pd.DataFrame(
        {
            "date": np.arange(x_pred_len, x_pred_len + len(x_pred)) - 1,
            "input": y_test[i].flatten(),
        }
    ).set_index("date", drop=True)

    _, axis = plt.subplots(1, 1, figsize=(12, 6))
    axis.plot(model_output, label="predicted", c="r")
    axis.plot(model_input, label="input")
    axis.plot(expected, label="expected", c="gray", ls="--")
    axis.legend()

    return axis


def train_val_split(
    data, n_steps_in: int, n_steps_out: int, val_samples: int
) -> np.array:
    """Divides sequence into train and validation sets based on size of validation set size.
    Uses _split_sequence to shape the outputs for use with DNN.

    Args:
        data: array of lists
        n_steps_in: number of input steps
        n_steps_out: number of output steps
        val_samples: number of validation samples

    Returns:
        four arrays

    """
    n_samples = val_samples - 1
    split_idx = len(data) - (n_steps_in + n_steps_out - 1) - n_samples
    data_train = data[:split_idx]
    data_valid = data[split_idx:]

    x_train_set, y_train_set = _split_sequence(data_train.values, n_steps_in, n_steps_out)
    x_valid_set, y_valid_set = _split_sequence(data_valid.values, n_steps_in, n_steps_out)

    print(
        f"Created {x_train_set.shape[0]} training samples, "
        f"and {x_valid_set.shape[0]} validation samples."
    )
    return x_train_set, y_train_set, x_valid_set, y_valid_set
