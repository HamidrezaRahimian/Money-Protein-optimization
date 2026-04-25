# Project Requirements – Geld zu Protein Optimierung

## 1. Official course requirements from the uploaded PDF

These are **mandatory** and should be treated as fixed grading criteria.

### Required deliverables
- Design a **genetic algorithm** following the lecture scheme from **Lecture 5, Slide 6**.
- Design **3 different representation alternatives**.
- **Implement and parameterize at least 2** of those 3 alternatives.
- Implement **2 baselines**:
  - **1 naive baseline**
  - **1 local search baseline**
- Compare the alternatives:
  - **2 own GA variants**
  - **1 naive approach**
  - **1 local search approach**
- Measure performance and show results using **suitable metrics and visualizations**.
- Write a **PDF documentation** of all design steps and decisions.
- Clearly document the **main responsible person per chapter/topic**.
- Use the **DHBW GitLab** repository for transparent collaboration.
- The whole group presents the work in a **20-minute presentation (+/- 1 minute)**.
- **All 3 team members** must speak and participate.
- Cameras should be **on** during the presentation.
- The presentation must be submitted to **Moodle by the day of the talk**.

### Grading weights
| Criterion | Weight |
|---|---:|
| Requirements analysis | 10 |
| Problem analysis | 10 |
| Representation alternatives | 15 |
| Design / implementation incl. operators | 20 |
| Parameterization study | 10 |
| Comparison of alternatives | 20 |
| Presentation style | 5 |
| Documentation / GitLab | 10 |
| **Total** | **100** |

---

## 2. Strict project-specific requirements for this optimization topic

### Problem statement
Build a system that finds a food selection or meal combination that gives the **best protein outcome under a limited budget** while also considering additional criteria such as:
- low total cost
- calorie suitability
- number of meals/servings
- taste/preference

### Functional requirements
1. The system must accept a **budget** (e.g. `20 €`) as an input.
2. The system must work on a dataset of food items with at least these attributes:
   - name
   - price
   - protein
   - calories
   - amount / servings / meal potential
   - taste score
3. A candidate solution must represent **which foods and how much of each food** are selected.
4. The algorithm must evaluate each candidate with a clearly defined **fitness function**.
5. The fitness should reward:
   - more protein
   - better taste
   - more usable meals/servings
6. The fitness should penalize:
   - exceeding the budget
   - poor calorie balance
   - unrealistic or infeasible combinations
7. The result must output:
   - selected foods
   - total price
   - total protein
   - total calories
   - estimated meals/servings
   - overall score / fitness

### Suggested hard constraints
These should be fixed and explicit in the analysis:
- `total_cost <= budget`
- all quantities must be non-negative and realistic
- optional calorie range can be defined depending on the scenario
- only available products from the dataset may be selected

### Optimization approach requirement
Because the task is multi-criteria, the team must choose and justify one of these:
- **weighted single fitness function**, or
- **multi-objective / Pareto-based evaluation**

For a first version, a **weighted normalized fitness function** is the simplest and most defendable choice.

---

## 3. Minimum algorithmic scope

### Representation alternatives (need 3 designs)
Possible alternatives for your report:
1. **Binary representation**: select or do not select each product.
2. **Integer quantity representation**: choose quantity per product.
3. **Meal-based representation**: encode grouped meal combinations instead of raw items.

### At least 2 must be implemented
Recommended implementation pair:
- **integer quantity GA**
- **binary GA**

### Required operators to define and justify
For each implemented GA:
- initialization
- selection
- crossover
- mutation
- replacement strategy
- elitism
- stopping criterion
- parameter settings

If possible, also mention whether any part is **dynamic/adaptive**.

---

## 4. Required baselines

You must implement and compare:
1. **Naive baseline**
   - e.g. greedy “buy highest protein-per-euro first”
2. **Local search baseline**
   - e.g. start with a feasible basket and improve by small swaps / quantity changes

---

## 5. Required evaluation plan

The comparison section must include measurable evidence.

### Suggested metrics
- best fitness achieved
- protein total
- protein per euro
- total cost
- calorie deviation from target
- number of servings/meals
- runtime
- convergence behavior over generations
- percentage of feasible solutions

### Required plots / figures
- fitness over generations
- comparison bar chart of final solution quality
- runtime comparison
- if useful: protein vs cost scatter plot

---

## 6. Documentation requirements

The written report should contain at least:
1. **Requirements analysis**
2. **Problem analysis**
   - objective function
   - decision vector
   - constraints
   - literature / related idea references
   - risks / assumptions
3. **3 representation alternatives**
4. **Implementation details** of the 2 chosen approaches
5. **Parameter study**
6. **Comparison and scientific conclusions**
7. **Team contribution transparency**

Every important decision should be justified with a short reason, not just described.

---

## 7. Recommended team split for 3 persons

### Person 1
- requirements analysis
- formal problem definition
- naive baseline

### Person 2
- GA representation alternative 1
- operators and implementation

### Person 3
- GA representation alternative 2
- local search and experiment evaluation

All 3 should contribute to documentation and presentation.

---

## 8. Non-negotiable checklist

Before submission, make sure the answer to all of these is **yes**:
- [ ] We have **3 representation designs** documented.
- [ ] We have **at least 2 GA variants implemented**.
- [ ] We have **1 naive** and **1 local search** baseline.
- [ ] We ran a **parameter study**.
- [ ] We compared all approaches with **metrics and figures**.
- [ ] We documented all major decisions with reasons.
- [ ] Responsibilities of each team member are visible.
- [ ] GitLab shows transparent collaboration.
- [ ] The presentation is ready for **20 minutes** and split across all members.

---

## 9. Working principle for this repository

From now on, this repository should follow this rule:

> **Do not build “just a protein maximizer”. Build a well-defined, documented, and experimentally compared optimization project that satisfies the DHBW grading criteria.**
