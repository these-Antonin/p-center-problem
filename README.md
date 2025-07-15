# p-center-problem
Gurobi code example to solve the classical p-center problem.

## Project Structure
```
p-center-problem
├── src
│   ├── main.py
│   ├── io_utils
│   │   ├── read_instance.py
│   │   ├── display_solution.py
│   │   ├── display_instance.py
│   │   └── generate_instance.py
│   ├── models
│   │   ├── capacitated.py
│   │   ├── classical
│   │   ├── failure.py
│   │   └── stratified.py
│   └── solver
│       └── solve.py
├── instances
│   ├── pmed
│   │   ├── pmed1.txt
│   │   ├── pmed2.txt
│   │   ├── ...
│   │   └── pmed40.txt
│   └── generated
│       └── ... (synthetic instances)
├── requirements.txt
└── README.md
```





## Installation
To set up the project, ensure you have Python and Gurobi installed. Then, install the required packages using:

```
python -m venv .venv
source ./venv/bin/activate

pip install -r requirements.txt
```

## Usage
1. Place your p-center problem instances in a suitable format in the designated directory.
2. Run the main application:

```
python -m src.main
```

3. Follow the prompts to read instances, solve the problem, and display the results.
or you can just 
```
python -m src.main <instance path>
```

#### Capacitated model

Several variants of the p-center problem exist in the literature, including the p-center problem with capacity constraints. 
This variant adds a demand to each node (customer) to differentiate them. We could compare the demands to the number of people in a city. Moreover, in the capacity constraints, we'll also differentiate between potential facilities. For example, if the facilities are schools, they would have different capacities (in terms of number of pupils)

To test the capacitated version of the p-center problem, you can run:
```
python -m src.main <instance path> --capacitated
```

**Please note that the instance must have the demand and capacity data.**

#### Model with failure foresight

A variant of the p-centers problem incorporates the notion of failures and failure management, where the objective is to predict future center assignments in the event of a main center failure. In the literature, several methods exist to solve this problem, such as the use of scenarios or the limitation to a single backup center.

In the model implemented here, we consider a single backup center per customer. In addition, we maintain capacity constraints. A single center can therefore serve as both the main center for some customers and the backup center for others. However, it is essential to respect capacity constraints, even in the event of a breakdown, i.e. when customers are reassigned following the failure of their main center. To guarantee this, we introduce an overload coefficient $\alpha$, representing an additional percentage of capacity, to accommodate redistributed customers.

Note that a backup center must necessarily be at least as close as a main center to each customer it serves. Moreover, for each customer, the main center and the backup center are necessarily different. 

To test the version with failure foresight, you can run:
```
python -m src.main <instance path> --failure <alpha>
```
where \<alpha\> is a float in [0,1]

#### Stratified model

The **stratified p-center problem** is a variant of the classical p-center problem that accounts for the heterogeneity of the population by introducing **strata**—subgroups defined by specific characteristics such as age groups, service levels, or geographic priorities.

Instead of optimizing coverage globally, the objective here is to **ensure good coverage within each stratum**. This is particularly useful when different segments of the population have **distinct service requirements**.

**How it works:**
- Each **stratum** corresponds to an **induced subgraph** of a larger, shared base graph. That is, all strata rely on the **same distance matrix and network structure**, but consider only a subset of nodes (clients and eligible centers) relevant to that stratum.
- Despite being defined separately, **center placement is shared across all strata**: opening a center in one stratum means it is opened in **every stratum**. This creates **dependencies between strata**, and the optimization must consider the **overlapping and sometimes conflicting needs** of each subgroup.
- The model also incorporates **failure tolerance** by assigning both a **primary** and a **backup** center to each client. As a result, **at least two centers must be opened per stratum** to ensure fallback service.

To test the version with failure foresight, you can run:
```
python -m src.main <instance path> --stratified <function>
```
where \<function\> is a string in ["A", "B", "AB"].

**Note**: The instance file must include stratification data, such as which clients and centers belong to which stratum.

### Instance Generator
This project includes a parameterizable generator for synthetic p-center problem instances.

#### Basic usage
You can generate test instances with custom size, layout, and options using the following command :
```
python src/io_utils/generate_instance.py \                                                   
    --n_clients 100 \
    --p_centers 5 \
    --space_type euclidean \
    --seed 42 \
    --compute_distances \
    --integer_distances \
    --show_plot \
    --capacitated \
    --tau 0.9 \
    --dem_min 5 \
    --dem_max 20 \
    --demand_distribution uniform
```

#### Common arguments
| Argument              | Description                                                                              |
| --------------------- | ---------------------------------------------------------------------------------------- |
| `--n_clients`         | Number of demand points (**required**)                                                   |
| `--p_centers`         | Number of centers to place (**required**)                                                |
| `--space_type`        | Spatial layout: `euclidean`, `grid`, or `random` (**required**)                          |
| `--seed`              | Random seed for reproducibility                                                          |
| `--distribution`      | Spatial distribution: `uniform` (default) or `clustered` (**only for euclidean/random**) |
| `--output_format`     | Format to save client coordinates: `csv` or `json`                                       |
| `--output_dir`        | Directory to save the generated files (default: `instances/generated`)                   |
| `--compute_distances` | If set, generates and saves the distance matrix in `.txt` format                         |
| `--integer_distances` | If set, distances will be rounded to integers                                            |
| `--show_plot`         | If set, displays a 2D scatter plot of the instance using matplotlib                      |



#### Output
- Coordinates (optionally)
- Distance matrix saved in .txt format compatible with existing instance parsers
- Plots (if --show_plot is enabled)

#### Coordinate Range
All coordinates are automatically generated in the range:
$[1, \sqrt{100*nclients}]$ following the litterature 


#### Capacitated instances
In many real-world applications, facilities (centers) have **limited capacity** and cannot serve an unlimited number of clients. To model this more realistically, we extend the classical p-center problem by introducing:

- **Demands** for each client: how much service or resource they require.
- **Capacities** for each center: the maximum total demand a center can serve.

This transforms the problem into a **Capacitated p-Center Problem (CpCP)**, which is more challenging but better reflects logistics, emergency response, and distribution systems.

To generate a **capacitated** instance, you must include the `--capacitated` flag and provide demand-related options:
```
python src/io_utils/generate_instance.py \
    --n_clients 100 \
    --p_centers 5 \
    --space_type euclidean \
    --seed 42 \
    --capacitated \
    --tau 0.9 \
    --dem_min 5 \
    --dem_max 20 \
    --demand_distribution uniform
```
##### Additional Required Arguments for Capacitated Instances:
| Argument                | Description                                                                 |
| ----------------------- | --------------------------------------------------------------------------- |
| `--capacitated`         | Enables capacitated generation mode                                         |
| `--tau`                 | coefficient $\in$ [0, 1]. Generally around 0.8 and 0.9. |
| `--dem_min`             | Minimum client demand                                                       |
| `--dem_max`             | Maximum client demand                                                       |
| `--demand_distribution` | `uniform` or `normal` (for demand generation)                               |

As for distances, capacities are generated following the literature : 

$$\left[\frac{(\sum_{i\in N}q_i)\cdot0.8}{p\cdot \tau}, \frac{(\sum_{i\in N}q_i)\cdot1.2}{p\cdot \tau}\right]$$

where $q_i$ is the demand of node $i$ so that $\sum_{i\in N}q_i$ is the total demand.

## Functions Overview
- **Reading Instances**: Use `read_instance.py` to load problem instances.
- **Displaying Solutions**: Use `display_solution.py` to show the results.
- **Displaying Instances**: Use `display_instance.py` to visualize the problem data.
- **Solving the Problem**: The `solve.py` file contains the logic to find the optimal solution using Gurobi.
- **Modeling**: The `models/` directory gather the different models to solve the p-center problem or one of its variants (Gurobi compatible)
- **Generator**: The `generate_instance.py` is used to generate instances according to different parameters

## Contributing
Feel free to contribute to the project by submitting issues or pull requests.
