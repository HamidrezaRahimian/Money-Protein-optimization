# Person 2: Representation Alternative B

## 1. Responsibility of Person 2

Person 2 is responsible for these parts:

- Representation Alternative B
- one full GA variant based on Representation B
- the local search baseline for the same representation
- mutation, crossover, selection and elitism design
- correct treatment of the budget constraint
- contribution to parameter study and evaluation

This role is clearly separable from the work of the other group members. That matters because the exam requires visible individual performance.

## 2. Representation Alternative B

### 2.1 Basic idea

Representation B models a basket as an integer quantity vector

\[
x = (x_1, x_2, \dots, x_n)
\]

with

- \(x_i\) = number of purchased units of product \(i\)
- \(x_i \in \mathbb{Z}\)
- \(0 \le x_i \le max\_units_i\)

Each position belongs to exactly one product in the dataset.
The value at that position tells us how many packages of that product are bought.

### 2.2 Example

If the first five products are Skyr, Magerquark, Hähnchenbrust, Thunfisch and Haferflocken, then

\[
x = (2, 0, 3, 1, 0)
\]

means:

- 2 units of product 1
- 0 units of product 2
- 3 units of product 3
- 1 unit of product 4
- 0 units of product 5

This encoding is close to the real shopping decision.

## 3. Why Representation B is suitable

Representation B is well suited because the products are sold as discrete packages and repeated purchases are allowed up to realistic upper bounds. The representation stores these quantities directly, so no extra decoding step is required.

Advantages:

- direct modelling of realistic shopping decisions
- compact and easy to interpret
- quantities can easily be evaluated for price, protein and calories
- small local changes correspond to realistic basket changes
- suitable for both genetic operators and local search operators

Disadvantages:

- the search space is larger than for a pure 0 or 1 representation
- crossover and mutation can produce baskets with poor budget usage
- strong constraint handling is necessary
- integer-valued genes require more careful operator design than binary genes

## 4. Objective and constraints

The main objective is the maximization of total protein:

\[
Protein(x) = \sum_{i=1}^{n} protein_i \cdot x_i
\]

The hard budget constraint is:

\[
\sum_{i=1}^{n} price_i \cdot x_i \le B
\]

with \(B = 50\) Euro.

Further soft criteria are considered only as secondary influences:

- portions
- category variety
- average taste
- calorie range of the whole basket

Protein remains the dominant criterion.

## 5. Fitness function used in the implementation

A penalty-based fitness function is used:

\[
f(x) = w_{prot} \cdot Protein(x)
+ w_{port} \cdot Portions(x)
+ w_{var} \cdot Variety(x)
+ w_{taste} \cdot Taste(x)
- w_{kcal} \cdot CaloriePenalty(x)
- w_{budget} \cdot \max(0, Cost(x) - B)^2
\]

The idea is simple:

- more protein is good
- more portions are slightly good
- more category variety is slightly good
- better average taste is slightly good
- unrealistic basket calories are punished a little
- budget violations are punished strongly

The quadratic budget penalty is intentional. A weak linear penalty would allow too many invalid solutions to remain attractive.

## 6. Constraint handling

Two mechanisms are used.

### 6.1 Penalty function

Invalid baskets are penalized strongly in the fitness function.

### 6.2 Repair mechanism

After crossover and mutation, a repair step removes units until the basket fits the budget.
The repair removes units from products with the worst protein per euro ratio first. This is more meaningful than deleting random items.

## 7. Shared team consistency

To keep the group project consistent, the implementation of Representation B can read the shared `config.json` file and the shared product CSV.

This means:

- the shared budget limit is reused
- shared GA settings can be reused in a controlled way
- shared fitness weights can be reused so that Representation B and Representation C remain comparable

Important distinction:

- the shared key `vector_length = 36` belongs to Representation C
- Representation B does **not** use that key, because Representation B always has vector length `n`, where `n` is the number of products

## 8. Genetic algorithm for Representation B

### 8.1 Initialization

The population is initialized by a mixture of:

- one greedy start solution based on protein per euro
- several random valid solutions

This gives both a strong starting point and enough diversity.

### 8.2 Parent selection

Tournament selection is used.
A few solutions are sampled randomly and the best of them becomes a parent.

Reason:

- simple
- stable
- moderate selection pressure
- easy to explain and implement

### 8.3 Crossover

Single-point crossover is used on the integer quantity vectors.

### 8.4 Mutation

Each gene can be changed by \(+1\) or \(-1\), while remaining inside

\[
[0, max\_units_i]
\]

With small probability, a gene is also reset to a random valid value to improve exploration.

### 8.5 Elitism and replacement

The best few individuals are copied unchanged to the next generation.
This prevents the best already found solutions from being lost.

### 8.6 Stopping criterion

The GA stops after a fixed number of generations.
This makes repeated experiments reproducible and easy to compare.

## 9. Local search baseline

The local search baseline is hill climbing on the same integer quantity vector.

### 9.1 Neighborhood move

A neighbor is generated by changing one randomly selected quantity by \(+1\) or \(-1\).
Sometimes a second quantity is changed as well.

### 9.2 Acceptance rule

A new basket is accepted only if it improves the fitness.

### 9.3 Restarts

Because hill climbing can get stuck in local optima, several restarts are used:

- one greedy start
- multiple random valid starts

### 9.4 Why local search fits this representation

The representation already stores quantities directly. Therefore, small integer changes correspond to natural basket adjustments, such as adding one Skyr or removing one expensive item.

## 10. Parameter study

The exam requires parametrization based on experiments. Therefore, the following parameters are tested for the GA:

- population size
- number of generations
- mutation rate
- elitism count

The implementation also produces repeated-run metrics and figures, including a boxplot and a convergence overview.
