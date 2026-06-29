# REPRODUCIBILITY GUIDE

This document provides detailed instructions to reproduce the experimental results presented in the paper accompanying this repository.

---

# 1. Prerequisites

## Hardware Requirements

The experiments were developed and tested on a standard workstation.

Recommended configuration:

* Multi-core CPU (Intel i7 / AMD Ryzen 7 or equivalent)
* 16 GB RAM (32 GB recommended)
* Ubuntu 22.04 LTS (recommended)
* Windows 11 (supported)
* Python ≥ 3.10

No GPU is required for the sampling experiments.

---

# 2. Software Requirements

Install Python dependencies:

```bash
pip install -r requirements.txt
```

The repository makes use of the following Python libraries:

* numpy
* pandas
* scikit-learn
* hdbscan
* matplotlib
* plotly
* streamlit

Additional dependencies may be required for the LMM Pipeline.

---

# 3. Repository Organization

The repository is divided into three main components.

| Folder              | Description                                                       |
| ------------------- | ----------------------------------------------------------------- |
| LMM Pipeline        | Traffic video processing and scenario extraction.                 |
| Sampling Algorithms | Implementation of all sampling techniques evaluated in the paper. |
| Graphic Plotter     | Streamlit application used to visualize the experimental results. |

---

# 4. Experimental Pipeline

The complete workflow is illustrated below.

```
Traffic Videos
        │
        ▼
LMM Pipeline
        │
        ▼
scenario_metrics.csv
        │
        ▼
Sampling Algorithms
        │
        ▼
Experimental CSV Results
        │
        ▼
Graphic Plotter
```

---

# 5. Dataset Generation

The LMM Pipeline processes raw traffic videos and generates a structured dataset.

The resulting dataset is:

```
scenario_metrics.csv
```

Each row corresponds to one driving scenario.

The dataset contains:

* collision outcome
* Time-To-Collision (TTC)
* Probability of Collision (PC)
* Operational Design Domain descriptors
* environmental features
* traffic-related features

This dataset is the input for all sampling algorithms.

---

# 6. Running the Sampling Algorithms

Move to the Sampling Algorithms folder.

```bash
cd "Sampling Algorithms"
```

The repository provides experimental drivers that automatically execute all experiments considered in the paper.

## Standard Experiments

Run:

```bash
python driver.py
```

The driver automatically evaluates:

* SRS
* SUPS
* SSRS
* RHC
* 2UPS
* DEEPEST

using all supported configurations.

---

## ODD Risk Experiments

To evaluate the ODD Risk auxiliary variable, execute:

```bash
python driver_oddrisk.py
```

---

# 7. Experimental Configurations

Each experiment is executed using multiple configurations.

## Sampling Algorithms

* SRS
* SUPS
* SSRS
* RHC
* 2UPS
* DEEPEST

---

## Operational Profiles

Four operational profiles are considered.

| Profile | Description                          |
| ------- | ------------------------------------ |
| P0      | Uniform operational profile          |
| P1      | Random operational profile           |
| P2      | Weather-oriented operational profile |
| P3      | Urban complexity operational profile |

---

## Auxiliary Variables

Three auxiliary variables are supported.

| Variable | Description              |
| -------- | ------------------------ |
| TTC      | Time-To-Collision        |
| PC       | Probability of Collision |
| ODD Risk | Composite ODD Risk Index |

---

## Partitioning Strategies

Depending on the sampling algorithm, the following partitioning methods are available.

* None
* ODD-based partitioning
* HDBSCAN clustering

---

## Sampling Budgets

The following sampling budgets are evaluated.

* 50
* 100
* 200
* 300
* 400

---

## Experimental Repetitions

Each configuration is independently repeated **30 times** using different random seeds.

---

# 8. Generated Results

The experimental drivers generate CSV files containing one row for each experimental repetition.

Each row stores:

* sampling method
* operational profile
* auxiliary variable
* partitioning strategy
* sampling budget
* run identifier
* estimated collision probability
* true collision probability
* observed failures
* execution time (when available)

The generated CSV files are directly used to reproduce the figures and tables reported in the paper.

---

# 9. Visualization

The experimental results can be explored using the Streamlit application.

Move to the Graphic Plotter folder and execute:

```bash
streamlit run app.py
```

The application provides interactive visualizations of:

* estimation accuracy
* collision probability estimates
* execution time
* observed failures
* algorithm comparisons
* operational profile comparisons

---

# 10. Expected Outputs

The execution of the complete experimental pipeline produces:

* processed scenario dataset
* experimental CSV files
* graphical visualizations
* comparative plots

These outputs correspond to the experimental evaluation presented in the accompanying publication.

---

# 11. Reproducibility Notes

To ensure reproducibility:

* use the same dataset;
* keep the default random seeds;
* execute all experiments without modifying the sampling parameters;
* use the provided experimental drivers.

The repository has been organized to allow straightforward reproduction of the complete experimental evaluation.

---

# 12. Troubleshooting

## Missing Python packages

Install all required dependencies:

```bash
pip install -r requirements.txt
```

---

## Streamlit not found

Install Streamlit:

```bash
pip install streamlit
```

---

## HDBSCAN import error

Install HDBSCAN:

```bash
pip install hdbscan
```

---

## CSV files not generated

Verify that the dataset has been successfully generated before executing the sampling experiments.

---

# Contact

For questions regarding the implementation or the experimental setup, please contact the repository maintainers through GitHub.
