# 2. Problemanalyse

---

## 2.1 Problemwissen

Das betrachtete Problem ist eine kombinatorische Optimierungsaufgabe aus dem Bereich der Einkaufs- bzw. Ressourcenoptimierung. Ziel ist es, aus einer gegebenen Menge diskreter Produkte eine Auswahl zu treffen, sodass ein maximaler Nutzen (Proteinmenge) unter einer harten Budgetrestriktion erreicht wird.

Typisch für diese Problemklasse ist, dass bereits kleine Änderungen in der Auswahl der Produkte stark unterschiedliche Auswirkungen auf Preis und Protein haben können. Dadurch entsteht ein komplexes Abwägungsproblem zwischen Kosten und Nutzen.

---

## 2.2 Genaue Charakterisierung von einfachen und schwierigen Instanzen

### Einfache Instanzen:
- wenige Produkte (<10)
- klare Dominanz einzelner Produkte (z. B. „bestes Protein/€-Verhältnis“ sticht hervor)
- kleiner Suchraum
- schnelle Konvergenz möglich

### Schwierige Instanzen:
- viele Produkte (>50)
- ähnliche Preis-/Proteinverhältnisse
- viele nahezu gleich gute Lösungen
- hoher Grad an Konkurrenz zwischen Lösungen
- große Suchraumdichte guter, aber suboptimal verteilter Lösungen

---

## 2.3 Existierende Lösungskandidaten und Benchmarks

Das Problem ist eng verwandt mit dem klassischen **Knapsack-Problem**. Daher existieren bereits bekannte Referenzansätze:

- Exakte Verfahren (Brute Force /Dynamische Programmierung (optimale Lösungen für begrenzte Größe))
- Greedy-Heuristiken (z. B. nach Protein/Preis-Verhältnis)
- genetische Algorithmen, Simulated Annealing

Als Benchmark dienen typischerweise:
- Brute-Force Lösungen für kleine Instanzen
- greedy-basierte Lösungen als Vergleichsbaseline
- bekannte Knapsack-Testinstanzen aus der Literatur: 

Die Branch and Bound Methode arbeitet nach dem Prinzip ”Teile und Herrsche”.
Eine vorliegende, schwer zu lösende, gemischt ganzzahlige Optimierungsaufgabe wird
immer wieder in mehrere Teilaufgaben ”aufgeteilt”, bis die einzelnen Teilaufgaben
”beherrschbar” geworden sind.

pseudo-polynomieller Algorithmus auf Basis einer dynamischen Programmierung, welcher in der Lage ist, das N P-schwere Problem in einer Laufzeit von O(nC) optimal zu lösen.

Der zweite Algorithmus zur approximativen Lösung von Rucksackproblemen ist die Linear
Programming (LP) Relaxation, bei der die binäre Bedingung der Entscheidungsvariable x
„relaxiert“ wird, wodurch das Problem mit Hilfe der linearen Optimierung lösbar ist

---

## 2.4 Existierende Heuristiken

Zur Lösung werden häufig folgende Heuristiken verwendet:

- Greedy-Auswahl nach höchstem Protein/Preis-Verhältnis -> bleiben bei localen Optima stecken
- lokale Suche (z. B. Tausch einzelner Produkte)
- randomisierte Konstruktion von Startlösungen
- genetische Algorithmen


Diese Verfahren dienen als Referenz für die Bewertung der Qualität eines neuen Ansatzes.

---

## 2.5 Definition des Optimierungsproblems

### Entscheidungsvektor
Der Lösungsvektor \(x\) beschreibt die Auswahl der Produkte:

- genauer Lösungsvektor bei einzelnen Darstellungen

---

### Zielfunktion
Maximierung des Gesamtproteins:

$$
f(x) = \sum_{i=1}^{n} Protein_i \cdot x_i
$$

---

### Zulässige Menge (Nebenbedingungen)
Eine Lösung ist nur gültig, wenn:

$$
\sum_{i=1}^{n} Preis_i \cdot x_i \le Budget
$$

---

### Nebenbedingungen
- harte Budgetrestriktion
- optional: Kalorienbegrenzung
- optional: Produktvielfalt

---

## 2.6 Literaturrecherche / GA-Bezug

Das Problem ist in der Literatur als Variante des **0/1- bzw. bounded Knapsack Problems** bekannt und wurde bereits häufig mit genetischen Algorithmen gelöst.

Typische Ansätze:
- klassische genetische Algorithmen (Bitstring-Codierung)
- reale Kodierungen (Integer Representation)
- Hybridansätze mit Repair-Mechanismen
- Penalty-basierte Fitnessfunktionen

Genetische Algorithmen sind besonders geeignet, da:
- der Suchraum exponentiell wächst
- viele lokale Optima existieren
- exakte Verfahren schnell unpraktikabel werden

---

## 2.7 Problemcharakteristika

---

- binär: \(2^n\) Suchraum 
- ganzzahlig: deutlich größer (potenziell unbegrenzt bzw. stark limitiert)

---
- Das Problem ist NP-schwer, da es eine Erweiterung des klassischen Knapsack-Problems darstellt.

---

- sehr viele lokale Optima bei großen Instanzen
- viele lokale Optima, besonders bei ähnlichen Preis-/Nutzenverhältnissen
- führt zu stagnierenden Suchprozessen bei einfachen Verfahren

---
- gute Lösungen sind stark ungleich verteilt
- viele Regionen enthalten nur mittelmäßige Lösungen
- optimale Lösungen liegen in engen, schwer auffindbaren Bereichen
- hohe Wahrscheinlichkeit für „Plateaus“ mit ähnlichen Fitnesswerten
