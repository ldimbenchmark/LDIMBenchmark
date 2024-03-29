### File level Interface

The file level interface is the low level interface of the benchmark suite.
It is designed to make it easy to implement the interface in any environment (docker, local, remote).

#### Input:

```
./input
 | -- demands/
 |     | -- <sensorname>.[csv|h5]
 | -- pressures/
 |     | -- <sensorname>.[csv|h5]
 | -- flows/
 |     | -- <sensorname>.[csv|h5]
 | -- levels/
 |     | -- <sensorname>.[csv|h5]
 | -- model.inp         # The water network model
 | -- dma.json          # Layout of the district metering zones it contains all nodes and pipes in the an area, enabling methods to be specific to each area.
 | -- dataset_info.yaml # Metadata File
 | -- leaks.csv         # Leaks with start and end time, as well as additional data.
 | -- leaks/
 |     | -- <leak_id>.csv # Timestamp data for leak outflows
```

> We trust the implementation of the Leakage detection method to use the correct implementation for each stage (e.g. doing online detection if told to instead of offline detection)

The following assumptions are made about the input data:

- the model is the leading datasource (meaning any sensor names in the other files must be present in the model)
  - The name of the csv files is corresponding to the name of the sensor in the inp file.
- the model is a valid EPANET model
  Maybe:

- the model might contain existing patterns

The following assumptions are not made:

- Timestamps are not required to be the same for all input files, to make it possible for the methods to do their own resample and interpolation of the data

Units for measurements are the same as in EPANET: https://epanet22.readthedocs.io/en/latest/back_matter.html#

|

#### Arguments

```
./args
 | -- options.yml   # Options for running the Method Runner (e.g. training and evaluation data timestamps, stage of the algorithm [training, detection_offline, detection_online] and goal (detection, localization), hyperparameters, etc.)

```

#### Output:

```
./output
 | -- detected_leaks.csv # The leaks found by the method
 | -- should_have_detected_leaks.csv
 | -- run_info.csv
 | -- debug
 | --  | -- ...      # Any information the method seems suitable as debug information. If the information should be plotted by the evaluation Methods the Timestamps should be the roughly the same as in the supplied dataset.
```
